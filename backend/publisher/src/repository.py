from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_and_lock_outbox_batch(
    session: AsyncSession,
    *,
    batch_size: int,
) -> list[dict]:
    result = await session.execute(
        text(
            """
            WITH locked AS (
                SELECT id, event_type, payload, attempts
                FROM outbox
                WHERE status = 'pending'
                  AND (next_attempt_at IS NULL OR next_attempt_at <= now())
                  AND (
                        locked_at IS NULL
                        OR locked_at <= (now() - interval '60 seconds')
                      )
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT :limit
            )
            UPDATE outbox o
            SET locked_at = now()
            FROM locked
            WHERE o.id = locked.id
            RETURNING o.id, o.event_type, o.payload, o.attempts
            """
        ),
        {"limit": batch_size},
    )
    rows = result.mappings().all()
    await session.commit()
    return [dict(r) for r in rows]


async def mark_outbox_sent(session: AsyncSession, *, outbox_id) -> None:
    await session.execute(
        text(
            """
            UPDATE outbox
            SET status = 'sent',
                sent_at = now(),
                locked_at = NULL,
                last_error = NULL
            WHERE id = :id
            """
        ),
        {"id": outbox_id},
    )
    await session.commit()


async def mark_outbox_failed(
    session: AsyncSession,
    *,
    outbox_id,
    error: str,
    attempts: int,
    max_attempts: int,
) -> None:
    delay_seconds = min(2 ** max(attempts, 0), 60)

    if (attempts + 1) >= max_attempts:
        await session.execute(
            text(
                """
                UPDATE outbox
                SET status = 'dead',
                    locked_at = NULL,
                    last_error = :err
                WHERE id = :id
                """
            ),
            {"id": outbox_id, "err": error[:10_000]},
        )
    else:
        await session.execute(
            text(
                """
                UPDATE outbox
                SET attempts = attempts + 1,
                    next_attempt_at = now() + (:delay_seconds * interval '1 second'),
                    locked_at = NULL,
                    last_error = :err
                WHERE id = :id
                """
            ),
            {"id": outbox_id, "err": error[:10_000], "delay_seconds": delay_seconds},
        )

    await session.commit()
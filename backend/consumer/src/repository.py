from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_payment_webhook_url(
    session: AsyncSession, *, payment_id: UUID
) -> str | None:
    result = await session.execute(
        text("SELECT webhook_url FROM payments WHERE id = :pid"),
        {"pid": payment_id},
    )
    row: Row | None = result.first()
    if row is None:
        return None
    return row[0]


async def update_payment_status(
    session: AsyncSession,
    *,
    payment_id: UUID,
    status: str,
    processed_at: datetime | None = None,
) -> bool:
    processed_at = processed_at or datetime.now(timezone.utc)
    result = await session.execute(
        text(
            """
            UPDATE payments
            SET status = :status,
                processed_at = :processed_at
            WHERE id = :pid
            """
        ),
        {"pid": payment_id, "status": status, "processed_at": processed_at},
    )
    await session.commit()
    return result.rowcount > 0


import asyncio

from faststream.rabbit import RabbitBroker

from .settings import settings
from .database import AsyncSessionFactory, check_db_connection, engine_dispose
from .repository import fetch_and_lock_outbox_batch, mark_outbox_failed, mark_outbox_sent

broker = RabbitBroker(settings.rabbitmq.url)


async def publisher_loop() -> None:
    while True:
        try:
            async with AsyncSessionFactory() as session:
                batch = await fetch_and_lock_outbox_batch(session, batch_size=settings.batch_size)

            if not batch:
                await asyncio.sleep(settings.poll_interval_s)
                continue
            
            print(f"[publisher] fetched batch size={len(batch)}", flush=True)

            async with AsyncSessionFactory() as session:
                for msg in batch:
                    outbox_id = msg["id"]
                    event_type = msg["event_type"]
                    payload = msg.get("payload") or {}
                    attempts = int(msg.get("attempts") or 0)

                    try:
                        print(
                            f"[publisher] publishing outbox_id={outbox_id} queue={event_type} attempts={attempts} payload={payload}",
                            flush=True,
                        )
                        await broker.publish(payload, queue=event_type)
                        await mark_outbox_sent(session, outbox_id=outbox_id)
                        print(
                            f"[publisher] published outbox_id={outbox_id} queue={event_type}",
                            flush=True,
                        )
                    except Exception as e:
                        await mark_outbox_failed(
                            session,
                            outbox_id=outbox_id,
                            error=str(e),
                            attempts=attempts,
                            max_attempts=settings.max_attempts,
                        )
                        print(
                            f"[publisher] publish failed outbox_id={outbox_id} queue={event_type} error={e}",
                            flush=True,
                        )
        except Exception as e:
            print(f"[publisher] loop error: {e}", flush=True)
            await asyncio.sleep(settings.poll_interval_s)


if __name__ == "__main__":
    async def main() -> None:
        if not await check_db_connection():
            raise RuntimeError("Failed to connect to database")
        
        await broker.connect()
        print("Publisher started")

        try:
            await publisher_loop()
        finally:
            await engine_dispose()

    asyncio.run(main())

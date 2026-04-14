import asyncio
import random
from uuid import UUID

from faststream.rabbit import RabbitBroker

from .database import AsyncSessionFactory
from .repository import get_payment_webhook_url, update_payment_status
from .webhook import send_webhook_with_retries


async def handle_payment_new_message(
    *,
    broker: RabbitBroker,
    message: dict,
    payments_new_queue: str,
    dlq_queue: str,
    max_message_attempts: int,
    max_webhook_attempts: int,
) -> None:
    attempt = int(message.get("_attempt") or 1)
    payment_id_raw = message.get("payment_id")
    if not payment_id_raw:
        print(f"[payments.new] skip: missing payment_id in {message!r}", flush=True)
        return

    payment_id = UUID(str(payment_id_raw))

    try:
        await asyncio.sleep(random.uniform(2.0, 5.0))

        succeeded = random.random() < 0.9
        new_status = "succeeded" if succeeded else "failed"

        async with AsyncSessionFactory() as session:
            updated = await update_payment_status(session, payment_id=payment_id, status=new_status)
            if not updated:
                raise RuntimeError(f"payment not found: {payment_id}")

            webhook_url = await get_payment_webhook_url(session, payment_id=payment_id)

        if webhook_url:
            await send_webhook_with_retries(
                url=webhook_url,
                payload={"payment_id": str(payment_id), "status": new_status},
                max_attempts=max_webhook_attempts,
            )

        print(
            f"[payments.new] processed payment_id={payment_id} status={new_status} attempt={attempt}",
            flush=True,
        )
    except Exception as e:
        if attempt >= max_message_attempts:
            await broker.publish(
                {
                    "payment_id": str(payment_id),
                    "_attempt": attempt,
                    "error": str(e),
                    "original": {k: v for k, v in message.items() if k != "error"},
                },
                queue=dlq_queue,
            )
            print(
                f"[payments.new] moved to DLQ payment_id={payment_id} attempt={attempt} err={e}",
                flush=True,
            )
            return

        next_attempt = attempt + 1
        backoff_s = min(2 ** (attempt - 1), 10)
        await asyncio.sleep(backoff_s)

        await broker.publish(
            {**{k: v for k, v in message.items() if k != "error"}, "_attempt": next_attempt},
            queue=payments_new_queue,
        )
        print(
            f"[payments.new] retry scheduled payment_id={payment_id} from_attempt={attempt} to_attempt={next_attempt} backoff_s={backoff_s} err={e}",
            flush=True,
        )


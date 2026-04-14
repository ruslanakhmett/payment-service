import asyncio
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from faststream.rabbit.schemas import RabbitQueue

from .settings import settings
from .database import check_db_connection, engine_dispose
from .payments_worker import handle_payment_new_message

broker = RabbitBroker(settings.rabbitmq.url)
app = FastStream(broker)

payments_new_queue = RabbitQueue(
    name=settings.rabbitmq.payments_new_queue,
    declare=False,
)


@broker.subscriber(payments_new_queue)
async def handle_payment_new(message: dict):
    await handle_payment_new_message(
        broker=broker,
        message=message,
        payments_new_queue=settings.rabbitmq.payments_new_queue,
        dlq_queue=settings.rabbitmq.payments_new_dlq_queue,
        max_message_attempts=settings.max_message_attempts,
        max_webhook_attempts=settings.max_webhook_attempts,
    )


if __name__ == "__main__":
    async def main() -> None:
        if not await check_db_connection():
            raise RuntimeError("Failed to connect to database")
        
        await broker.connect()
        print("Consumer started")

        try:
            await app.run()
        finally:
            await engine_dispose()

    asyncio.run(main())

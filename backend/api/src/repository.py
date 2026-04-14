from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionFactory
from .models import Outbox, Payment


async def get_payment_by_idempotency_key(*, idempotency_key: str) -> Payment | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )


async def get_payment_by_id(*, payment_id) -> Payment | None:
    async with AsyncSessionFactory() as session:
        return await session.get(Payment, payment_id)


async def check_db_health() -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(text("SELECT 1"))


async def create_payment(
    *,
    amount,
    currency: str,
    description: str,
    metadata: dict,
    webhook_url: str | None,
    idempotency_key: str,
) -> Payment:
    async with AsyncSessionFactory() as session:
        payment = Payment(
            amount=amount,
            currency=currency,
            description=description,
            metadata_=metadata,
            webhook_url=webhook_url,
            status="pending",
            idempotency_key=idempotency_key,
        )
        session.add(payment)

        # Outbox event
        outbox_event = Outbox(
            event_type="payments.new",
            payload={},  # filled after flush
            status="pending",
            attempts=0,
        )
        session.add(outbox_event)

        try:
            # Flush to get payment.id, then update outbox payload inside same transaction.
            await session.flush()
            outbox_event.payload = {"payment_id": str(payment.id)}

            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise

        await session.refresh(payment)
        return payment


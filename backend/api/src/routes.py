from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .auth import verify_api_key
from .models import Payment
from .schemas import PaymentAccepted, PaymentCreate, PaymentDetail
from .repository import create_payment as repo_create_payment
from .repository import check_db_health as repo_check_db_health
from .repository import get_payment_by_id as repo_get_payment_by_id
from .repository import get_payment_by_idempotency_key as repo_get_payment_by_idempotency_key

payments_router = APIRouter(
    prefix="/payments", tags=["payments"], dependencies=[Depends(verify_api_key)]
)
system_router = APIRouter(
    prefix="/system", tags=["system"], dependencies=[Depends(verify_api_key)]
)
webhook_router = APIRouter(prefix="/webhook", tags=["webhook"])


def _to_accepted(p: Payment) -> PaymentAccepted:
    return PaymentAccepted(payment_id=p.id, status=p.status, created_at=p.created_at)


def _to_detail(p: Payment) -> PaymentDetail:
    return PaymentDetail(
        payment_id=p.id,
        amount=p.amount,
        currency=p.currency,
        description=p.description,
        metadata=p.metadata_ or {},
        webhook_url=p.webhook_url,
        status=p.status,
        created_at=p.created_at,
        processed_at=p.processed_at,
    )


@payments_router.post("", response_model=PaymentAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> PaymentAccepted:
    if not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    # Fast path: return existing payment for same Idempotency-Key
    existing = await repo_get_payment_by_idempotency_key(idempotency_key=idempotency_key)
    if existing is not None:
        return _to_accepted(existing)

    try:
        payment = await repo_create_payment(
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            metadata=payload.metadata,
            webhook_url=str(payload.webhook_url),
            idempotency_key=idempotency_key,
        )
    except IntegrityError:
        # Race condition: another request inserted the same idempotency_key
        existing = await repo_get_payment_by_idempotency_key(idempotency_key=idempotency_key)
        if existing is not None:
            return _to_accepted(existing)
        raise

    return _to_accepted(payment)


@payments_router.get("/{payment_id}", response_model=PaymentDetail)
async def get_payment(
    payment_id: UUID,
) -> PaymentDetail:
    payment = await repo_get_payment_by_id(payment_id=payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return _to_detail(payment)


@system_router.get("/health")
async def health_check():
    try:
        await repo_check_db_health()
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": "database unavailable", "detail": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Content-Type": "application/json"},
        )

    return JSONResponse(
        content={"status": "ok", "message": "service is running"},
        status_code=status.HTTP_200_OK,
        headers={"Content-Type": "application/json"},
    )


# http://api:5005/api/v1/webhook/test
@webhook_router.post("/test", status_code=status.HTTP_200_OK)
async def accept_webhook_test(payload: dict):
    print(f"[webhook:test] received: {payload!r}")
    return {"ok": True}

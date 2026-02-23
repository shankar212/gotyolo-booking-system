from uuid import UUID
from enum import Enum
from pydantic import BaseModel

class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"

class PaymentWebhook(BaseModel):
    booking_id: UUID
    status: PaymentStatus
    idempotency_key: str

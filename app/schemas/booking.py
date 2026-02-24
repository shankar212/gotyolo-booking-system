from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.enums import BookingState

class BookingCreate(BaseModel):
    user_id: UUID
    num_seats: int = Field(..., gt=0)

class BookingResponse(BaseModel):
    id: UUID
    trip_id: UUID
    user_id: UUID
    num_seats: int
    state: BookingState
    price_at_booking: Decimal
    expires_at: datetime
    refund_amount: Optional[Decimal] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

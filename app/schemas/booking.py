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
    price_at_booking: Decimal = Field(..., example="1200.00")
    expires_at: datetime
    refund_amount: Optional[Decimal] = Field(None, example="0.00")
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: format(v, ".2f")
        }

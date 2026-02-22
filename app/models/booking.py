import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import BookingState

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    num_seats = Column(Integer, nullable=False)
    state = Column(Enum(BookingState), nullable=False, default=BookingState.PENDING_PAYMENT)
    price_at_booking = Column(Numeric(precision=10, scale=2), nullable=False)
    payment_reference = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    refund_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    trip = relationship("Trip", backref="bookings")

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
from app.models.enums import TripStatus

class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    max_capacity = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    status = Column(Enum(TripStatus), nullable=False, default=TripStatus.DRAFT)
    refundable_until_days_before = Column(Integer, nullable=False, default=7)
    cancellation_fee_percent = Column(Integer, nullable=False, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("available_seats >= 0", name="available_seats_non_negative"),
    )

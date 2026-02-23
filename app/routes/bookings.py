from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.enums import TripStatus, BookingState
from app.schemas.booking import BookingCreate, BookingResponse

router = APIRouter(prefix="/trips", tags=["bookings"])

@router.post("/{trip_id}/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    trip_id: UUID,
    booking_in: BookingCreate,
    db: Session = Depends(get_db)
):
    # 1. Start a database transaction (FastAPI/SQLAlchemy session handles this)
    # 2. Fetch the Trip row using SELECT FOR UPDATE
    trip = db.query(Trip).filter(Trip.id == trip_id).with_for_update().first()

    # 3. If trip does not exist or status is not PUBLISHED → return 404
    if not trip or trip.status != TripStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or not published"
        )

    # 4. If available_seats < num_seats → return 409 Conflict
    if trip.available_seats < booking_in.num_seats:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough seats available. Requested: {booking_in.num_seats}, Available: {trip.available_seats}"
        )

    # 5. If seats available:
    # - Decrement available_seats
    trip.available_seats -= booking_in.num_seats

    # - Create Booking
    # price_at_booking = trip.price * num_seats
    # expires_at = now + 15 minutes
    total_price = trip.price * booking_in.num_seats
    expiry_time = datetime.utcnow() + timedelta(minutes=15)

    booking = Booking(
        trip_id=trip.id,
        user_id=booking_in.user_id,
        num_seats=booking_in.num_seats,
        state=BookingState.PENDING_PAYMENT,
        price_at_booking=total_price,
        expires_at=expiry_time
    )

    db.add(booking)

    # 6. Commit transaction
    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the booking"
        )

    # 7. Return booking details in response
    return booking

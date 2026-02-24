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
booking_router = APIRouter(prefix="/bookings", tags=["bookings"])

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


@booking_router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: UUID,
    db: Session = Depends(get_db)
):
    # 1. Start a database transaction (handled by session)
    # 2. Lock booking row using with_for_update()
    booking = db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # 3. If booking.state is EXPIRED or CANCELLED → return 409
    if booking.state in [BookingState.EXPIRED, BookingState.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking cannot be cancelled in its current state: {booking.state}"
        )
    
    # 4. Lock associated Trip row
    trip = db.query(Trip).filter(Trip.id == booking.trip_id).with_for_update().first()
    if not trip:
        # This shouldn't happen based on DB constraints, but safety first
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated trip not found"
        )
    
    # 5. Determine cutoff
    cutoff_date = trip.start_date - timedelta(days=trip.refundable_until_days_before)
    now = datetime.utcnow()
    
    # 6. If current time is before cutoff
    if now < cutoff_date:
        # refund_amount = price_at_booking * (1 - cancellation_fee_percent/100)
        refund_percent = 1 - (trip.cancellation_fee_percent / 100.0)
        booking.refund_amount = booking.price_at_booking * refund_percent
        # release seats back to trip
        trip.available_seats += booking.num_seats
    else:
        # 7. If current time is after cutoff
        booking.refund_amount = 0
        # do not release seats (implied by doing nothing)
    
    # 8. Update booking.state to CANCELLED
    booking.state = BookingState.CANCELLED
    
    # 9. Set cancelled_at timestamp
    booking.cancelled_at = now
    
    # 10. Commit transaction
    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while cancelling the booking"
        )
    
    return booking

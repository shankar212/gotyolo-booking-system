from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.booking import Booking
from app.models.trip import Trip
from app.models.enums import BookingState
from app.schemas.payment import PaymentWebhook, PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/webhook", status_code=status.HTTP_200_OK)
def handle_webhook(
    webhook_in: PaymentWebhook,
    db: Session = Depends(get_db)
):
    # 1. Always return HTTP 200 (payment providers require this)
    
    # 2. If idempotency_key already exists in database → return 200 immediately
    existing_booking = db.query(Booking).filter(
        Booking.idempotency_key == webhook_in.idempotency_key
    ).first()
    if existing_booking:
        return {"status": "already_processed"}

    # 3. Start a transaction
    # 4. Lock the booking row using with_for_update()
    booking = db.query(Booking).filter(
        Booking.id == webhook_in.booking_id
    ).with_for_update().first()

    # 5. If booking not found → return 200
    if not booking:
        return {"status": "booking_not_found"}

    # 6. If booking.state is not PENDING_PAYMENT → return 200
    if booking.state != BookingState.PENDING_PAYMENT:
        return {"status": "invalid_state"}

    # 7. If status is "success":
    if webhook_in.status == PaymentStatus.SUCCESS:
        booking.state = BookingState.CONFIRMED
    
    # 8. If status is "failed":
    elif webhook_in.status == PaymentStatus.FAILED:
        booking.state = BookingState.EXPIRED
        
        # Increment trip.available_seats by booking.num_seats
        trip = db.query(Trip).filter(Trip.id == booking.trip_id).with_for_update().first()
        if trip:
            trip.available_seats += booking.num_seats

    # 9. Store idempotency_key on booking
    booking.idempotency_key = webhook_in.idempotency_key

    # 10. Commit transaction
    try:
        db.commit()
    except Exception:
        db.rollback()
        # Still return 200 to satisfy provider, but log or handle internally if needed
        return {"status": "error_during_processing"}

    return {"status": "processed"}

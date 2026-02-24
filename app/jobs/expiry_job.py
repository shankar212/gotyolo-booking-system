from datetime import datetime
from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.trip import Trip
from app.models.enums import BookingState

def expire_pending_bookings():
    """
    Background job to expire bookings that are in PENDING_PAYMENT state
    and have passed their expires_at time.
    """
    db = SessionLocal()
    try:
        # 1. Start transaction (implicit in SessionLocal if not autocommit)
        
        # 2. Find expired bookings in PENDING_PAYMENT state
        now = datetime.utcnow()
        expired_bookings = (
            db.query(Booking)
            .filter(
                Booking.state == BookingState.PENDING_PAYMENT,
                Booking.expires_at < now
            )
            .with_for_update() # 3. Lock affected bookings
            .all()
        )
        
        if not expired_bookings:
            return

        for booking in expired_bookings:
            # 4. Set state to EXPIRED
            booking.state = BookingState.EXPIRED
            
            # 5. Lock associated Trip row
            trip = db.query(Trip).filter(Trip.id == booking.trip_id).with_for_update().first()
            if trip:
                # 6. Increment available_seats
                trip.available_seats += booking.num_seats
        
        # 7. Commit transaction
        db.commit()
        print(f"[{datetime.now()}] Expired {len(expired_bookings)} bookings.")
    except Exception as e:
        db.rollback()
        print(f"[{datetime.now()}] Error in expire_pending_bookings: {e}")
    finally:
        db.close()

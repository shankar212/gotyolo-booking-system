import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from app.db.session import SessionLocal
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.enums import TripStatus, BookingState

def seed_data():
    db = SessionLocal()
    try:
        # 1. Cleanup existing data (Optional, but helps with clean seeds)
        db.query(Booking).delete()
        db.query(Trip).delete()
        db.commit()

        now = datetime.utcnow()

        # 2. Create Sample Trips
        trips = [
            Trip(
                id=uuid.uuid4(),
                title="Alpine Adventure",
                destination="Swiss Alps",
                start_date=now + timedelta(days=5),  # At risk (within 7 days)
                end_date=now + timedelta(days=12),
                price=Decimal("1200.00"),
                max_capacity=20,
                available_seats=20,
                status=TripStatus.PUBLISHED,
                refundable_until_days_before=7,
                cancellation_fee_percent=15
            ),
            Trip(
                id=uuid.uuid4(),
                title="Tropical Paradise",
                destination="Maldives",
                start_date=now + timedelta(days=30),
                end_date=now + timedelta(days=37),
                price=Decimal("2500.00"),
                max_capacity=10,
                available_seats=10,
                status=TripStatus.PUBLISHED,
                refundable_until_days_before=14,
                cancellation_fee_percent=20
            ),
            Trip(
                id=uuid.uuid4(),
                title="Desert Safari",
                destination="Dubai",
                start_date=now + timedelta(days=3),  # At risk
                end_date=now + timedelta(days=5),
                price=Decimal("800.00"),
                max_capacity=50,
                available_seats=50,
                status=TripStatus.PUBLISHED,
                refundable_until_days_before=2,
                cancellation_fee_percent=10
            ),
            Trip(
                id=uuid.uuid4(),
                title="Urban Explorer",
                destination="Tokyo",
                start_date=now + timedelta(days=60),
                end_date=now + timedelta(days=70),
                price=Decimal("1800.00"),
                max_capacity=15,
                available_seats=15,
                status=TripStatus.DRAFT,
                refundable_until_days_before=30,
                cancellation_fee_percent=25
            )
        ]

        db.add_all(trips)
        db.commit()

        # 3. Create Sample Bookings
        # Trip 1: Alpine Adventure (Cap: 20, Max-At-Risk if < 50% occupancy)
        # We'll make it at-risk with 4/20 seats (20%)
        bookings = [
            # Confirmed
            Booking(
                trip_id=trips[0].id,
                user_id=uuid.uuid4(),
                num_seats=2,
                state=BookingState.CONFIRMED,
                price_at_booking=Decimal("2400.00"),
                expires_at=now + timedelta(minutes=15)
            ),
            # Pending
            Booking(
                trip_id=trips[0].id,
                user_id=uuid.uuid4(),
                num_seats=2,
                state=BookingState.PENDING_PAYMENT,
                price_at_booking=Decimal("2400.00"),
                expires_at=now + timedelta(minutes=15)
            ),
            # Cancelled with refund
            Booking(
                trip_id=trips[0].id,
                user_id=uuid.uuid4(),
                num_seats=1,
                state=BookingState.CANCELLED,
                price_at_booking=Decimal("1200.00"),
                expires_at=now - timedelta(hours=1),
                cancelled_at=now - timedelta(minutes=30),
                refund_amount=Decimal("1020.00") # 1200 * 0.85
            ),
            
            # Trip 2: Tropical Paradise (Cap: 10)
            # Confirmed 8 seats (80% occupancy)
            Booking(
                trip_id=trips[1].id,
                user_id=uuid.uuid4(),
                num_seats=4,
                state=BookingState.CONFIRMED,
                price_at_booking=Decimal("10000.00"),
                expires_at=now + timedelta(minutes=15)
            ),
            Booking(
                trip_id=trips[1].id,
                user_id=uuid.uuid4(),
                num_seats=4,
                state=BookingState.CONFIRMED,
                price_at_booking=Decimal("10000.00"),
                expires_at=now + timedelta(minutes=15)
            ),
            # Expired
            Booking(
                trip_id=trips[1].id,
                user_id=uuid.uuid4(),
                num_seats=2,
                state=BookingState.EXPIRED,
                price_at_booking=Decimal("5000.00"),
                expires_at=now - timedelta(minutes=30)
            ),

            # Trip 3: Desert Safari (Cap: 50)
            # 5 confirmed seats (10%) - At Risk
            Booking(
                trip_id=trips[2].id,
                user_id=uuid.uuid4(),
                num_seats=5,
                state=BookingState.CONFIRMED,
                price_at_booking=Decimal("4000.00"),
                expires_at=now + timedelta(minutes=15)
            ),
            # Cancelled no refund
            Booking(
                trip_id=trips[2].id,
                user_id=uuid.uuid4(),
                num_seats=10,
                state=BookingState.CANCELLED,
                price_at_booking=Decimal("8000.00"),
                expires_at=now - timedelta(days=1),
                cancelled_at=now - timedelta(hours=1),
                refund_amount=Decimal("0.00")
            )
        ]

        db.add_all(bookings)
        db.commit()

        # 4. Synchronize Trip available_seats
        for trip in trips:
            # sum seats for CONFIRMED and PENDING_PAYMENT
            consumed_seats = db.query(Booking).filter(
                Booking.trip_id == trip.id,
                Booking.state.in_([BookingState.CONFIRMED, BookingState.PENDING_PAYMENT])
            ).with_entities(Booking.num_seats).all()
            
            total_consumed = sum(s[0] for s in consumed_seats)
            trip.available_seats = trip.max_capacity - total_consumed
        
        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

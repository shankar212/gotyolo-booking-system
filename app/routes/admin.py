from uuid import UUID
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import get_db
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.enums import BookingState
from app.schemas.admin import TripMetricsResponse, AtRiskTripResponse, FinancialMetrics

router = APIRouter(prefix="/admin/trips", tags=["admin"])

@router.get("/{trip_id}/metrics", response_model=TripMetricsResponse)
def get_trip_metrics(trip_id: UUID, db: Session = Depends(get_db)):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Aggregate data from bookings
    # booked_seats: sum of num_seats for CONFIRMED bookings
    # gross_revenue: sum of price_at_booking for CONFIRMED bookings
    # refunds_issued: sum of refund_amount
    metrics = db.query(
        func.sum(case((Booking.state == BookingState.CONFIRMED, Booking.num_seats), else_=0)).label("booked_seats"),
        func.sum(case((Booking.state == BookingState.CONFIRMED, Booking.price_at_booking), else_=0)).label("gross_revenue"),
        func.sum(func.coalesce(Booking.refund_amount, 0)).label("refunds_issued")
    ).filter(Booking.trip_id == trip_id).first()

    booked_seats = metrics.booked_seats or 0
    gross_revenue = metrics.gross_revenue or Decimal("0.00")
    refunds_issued = metrics.refunds_issued or Decimal("0.00")
    
    # Booking summary: counts by state
    summary_rows = db.query(
        Booking.state, 
        func.count(Booking.id)
    ).filter(Booking.trip_id == trip_id).group_by(Booking.state).all()
    
    booking_summary = {state.value: count for state, count in summary_rows}
    
    # Ensure all states are present in summary if needed, but dict comprehension is fine
    
    # Calculate occupancy
    occupancy_percent = (booked_seats / trip.max_capacity) * 100 if trip.max_capacity > 0 else 0
    
    return TripMetricsResponse(
        trip_id=trip.id,
        title=trip.title,
        occupancy_percent=occupancy_percent,
        total_seats=trip.max_capacity,
        booked_seats=booked_seats,
        available_seats=trip.available_seats,
        booking_summary=booking_summary,
        financial=FinancialMetrics(
            gross_revenue=gross_revenue,
            refunds_issued=refunds_issued,
            net_revenue=gross_revenue - refunds_issued
        )
    )

@router.get("/at-risk", response_model=List[AtRiskTripResponse])
def get_at_risk_trips(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    next_week = now + timedelta(days=7)
    
    # Trips starting within next 7 days
    # occupancy_percent < 50%
    # We need to join with bookings to calculate current occupancy
    
    # booked_seats calculation joined per trip
    query = db.query(
        Trip,
        func.sum(case((Booking.state == BookingState.CONFIRMED, Booking.num_seats), else_=0)).label("booked_seats")
    ).outerjoin(Booking, Trip.id == Booking.trip_id)\
     .filter(Trip.start_date >= now, Trip.start_date <= next_week)\
     .group_by(Trip.id)
    
    results = query.all()
    at_risk = []
    
    for trip, booked_seats in results:
        booked_seats = booked_seats or 0
        occupancy_percent = (booked_seats / trip.max_capacity) * 100 if trip.max_capacity > 0 else 0
        
        if occupancy_percent < 50:
            at_risk.append(AtRiskTripResponse(
                trip_id=trip.id,
                title=trip.title,
                start_date=trip.start_date.isoformat(),
                occupancy_percent=occupancy_percent,
                max_capacity=trip.max_capacity,
                available_seats=trip.available_seats
            ))
            
    return at_risk

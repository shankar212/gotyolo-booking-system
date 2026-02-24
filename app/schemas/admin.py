from uuid import UUID
from pydantic import BaseModel
from typing import Dict, List
from decimal import Decimal

class FinancialMetrics(BaseModel):
    gross_revenue: Decimal
    refunds_issued: Decimal
    net_revenue: Decimal

class TripMetricsResponse(BaseModel):
    trip_id: UUID
    title: str
    occupancy_percent: float
    total_seats: int
    booked_seats: int
    available_seats: int
    booking_summary: Dict[str, int]
    financial: FinancialMetrics

class AtRiskTripResponse(BaseModel):
    trip_id: UUID
    title: str
    start_date: str
    occupancy_percent: float
    max_capacity: int
    available_seats: int

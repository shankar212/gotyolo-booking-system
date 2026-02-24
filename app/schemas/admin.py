from uuid import UUID
from pydantic import BaseModel, Field
from typing import Dict, List
from decimal import Decimal

class FinancialMetrics(BaseModel):
    gross_revenue: Decimal = Field(..., example="1200.00")
    refunds_issued: Decimal = Field(..., example="0.00")
    net_revenue: Decimal = Field(..., example="1200.00")

    class Config:
        json_encoders = {
            Decimal: lambda v: format(v, ".2f")
        }

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

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here to register them with metadata
from app.models.trip import Trip
from app.models.booking import Booking

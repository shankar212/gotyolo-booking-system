from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.routes import bookings

# Create tables for development
Base.metadata.create_all(bind=engine)

app = FastAPI(title="gotyolo-booking-system")

app.include_router(bookings.router)

@app.get("/")
async def root():
    return {"message": "Welcome to gotyolo-booking-system API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

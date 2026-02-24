from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes import bookings, payments
from app.jobs.expiry_job import expire_pending_bookings

# Create tables for development
Base.metadata.create_all(bind=engine)

app = FastAPI(title="gotyolo-booking-system")

# Initialize and start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(expire_pending_bookings, "interval", minutes=1)

@app.on_event("startup")
def startup_event():
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

app.include_router(bookings.router)
app.include_router(bookings.booking_router)
app.include_router(payments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to gotyolo-booking-system API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

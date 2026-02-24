from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes import bookings, payments, admin
from app.jobs.expiry_job import expire_pending_bookings

app = FastAPI(title="gotyolo-booking-system")

# Initialize and start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(expire_pending_bookings, "interval", minutes=1)

@app.on_event("startup")
def on_startup():
    # Create tables safely after DB is ready
    Base.metadata.create_all(bind=engine)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

app.include_router(bookings.router)
app.include_router(bookings.booking_router)
app.include_router(payments.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Welcome to gotyolo-booking-system API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

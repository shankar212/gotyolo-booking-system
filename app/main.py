from fastapi import FastAPI

app = FastAPI(title="gotyolo-booking-system")

@app.get("/")
async def root():
    return {"message": "Welcome to gotyolo-booking-system API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

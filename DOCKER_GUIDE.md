# Docker Run Guide

Follow these steps to build and run the `gotyolo-booking-system` using Docker.

> [!NOTE]
> If you are using Docker Desktop, use `docker compose` instead of `docker-compose`.

## 1. Build and Start Services

Run the following command to build the images and start the PostgreSQL and FastAPI containers in detached mode:

```bash
docker compose up --build -d
```

## 2. Verify Services are Running

Check the status of the containers:

```bash
docker compose ps
```

You should see two containers: `gotyolo_app` and `gotyolo_db`.

## 3. Check Logs

To view the logs for the FastAPI application:

```bash
docker compose logs -f app
```

## 4. Verify Functionality

### Health Endpoint
Verify the API is running by visiting [http://localhost:8000/health](http://localhost:8000/health) or using `curl`:

```bash
curl http://localhost:8000/health
```
**Expected Response:** `{"status": "healthy"}`

### Database Connection
The application automatically initializes tables on startup. You can check the logs for any database connection errors.

## 5. Stop Services

To stop and remove the containers:

```bash
docker compose down
```

To stop and remove containers plus the database volume (CAUTION: this deletes all data):

```bash
docker compose down -v
```

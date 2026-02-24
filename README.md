# gotyolo-booking-system

## Project Overview
The gotyolo-booking-system is a high-concurrency backend service for the GoTyolo travel platform. It manages the complete lifecycle of trip bookings, including seat availability tracking, automated expiration of pending payments, financial refund calculations, and administrative performance metrics. The system is designed for high reliability and data consistency in a distributed environment.

## Tech Stack
- **FastAPI**: Chosen for its high performance, native support for asynchronous programming, and automatic OpenAPI documentation.
- **PostgreSQL**: Used as the primary relational database for its robust transaction support and advanced data integrity features.
- **SQLAlchemy**: Employed as the ORM to provide type-safe database interactions and complex aggregation capabilities.
- **APScheduler**: Manages background tasks, specifically the automated expiration of unpaid bookings.
- **Docker + Docker Compose**: Orchestrates the application and database services, ensuring environment consistency and simplified deployment.

## Architecture Overview
The system implements a strict state machine for booking lifecycles:
`PENDING_PAYMENT` → `CONFIRMED` → `CANCELLED` | `EXPIRED`

### Core Principles
- **Transaction Boundaries**: Every critical operation (booking, payment, cancellation) is executed within a database transaction to ensure atomicity.
- **Row-Level Locking**: High-concurrency endpoints utilize `SELECT ... FOR UPDATE` to lock specific trip or booking rows, preventing race conditions during status updates or seat decrements.
- **Idempotency**: Webhook handlers use idempotency keys to ensure payment processing is performed exactly once, even in the event of provider retries.
- **Background Processes**: An automated job monitors the `expires_at` timestamp for `PENDING_PAYMENT` bookings, transitioning them to `EXPIRED` and releasing seats back to the trip inventory if payment is not confirmed within 15 minutes.

## Concurrency & Overbooking Prevention
The system prevents overselling by performing seat availability checks inside a locked transaction. When a booking request arrives:
1. The relevant Trip row is locked (`FOR UPDATE`).
2. `available_seats` is verified against the requested amount.
3. If sufficient, the record is updated in the same transaction.

Under high load (e.g., 500 simultaneous requests for the same trip), PostgreSQL serializes access to the locked row. While this ensures zero overbooking, the database lock wait becomes a performance bottleneck for that specific row. Scaling considerations for higher loads include introducing a distributed caching layer or implementing a reservation-token mechanism to offload the primary database.

## Refund & Cancellation Logic
Cancellations are governed by trip-specific policies:
- **refundable_until_days_before**: This parameter defines the cutoff date for refunds.
- **cancellation_fee_percent**: If cancelled before the cutoff, the refund is calculated as `price * (1 - fee%)`.
- **Seat Release**: Seats are released back to the `available_seats` pool only if the cancellation occurs before the refundable cutoff. After this period, the seat remains occupied even if the booking is cancelled.

## Admin Metrics
Dedicated administrative endpoints provide real-time insights:
- **Financial Aggregation**: Calculates Gross Revenue, Refunds, and Net Revenue at the database level using SQLAlchemy functional aggregations.
- **At-Risk Detection**: Identifies trips starting within 7 days that have less than 50% occupancy, allowing for proactive marketing or operations interventions.
- **Booking Summaries**: Provides a distribution of booking states for each trip.

## Denormalization Justification
The `available_seats` field is denormalized on the `Trip` table for performance. Calculating availability in real-time by summing confirmed/pending bookings across millions of records is computationally expensive for every request.
- **Risk**: Potential drift between the trip count and the sum of bookings.
- **Mitigation**: Consistency is maintained through strict transaction boundaries and row-level locking. The seat count is modified only in the same transaction that creates or expires a booking.

## Setup Instructions
### Deployment
```bash
docker compose up --build -d
```
### Database Seeding
To populate the system with professional test data:
```bash
docker exec -it gotyolo_app python -m app.db.seed
```
### Shutdown
```bash
docker compose down
```

## API Endpoints Summary
- `POST /trips/{id}/book`: Create a new booking (PENDING_PAYMENT).
- `POST /bookings/{id}/cancel`: Cancel an existing booking and calculate refund.
- `POST /payments/webhook`: Handle external payment success/failure notifications.
- `GET /admin/trips/{id}/metrics`: Retrieve detailed financial and occupancy data.
- `GET /admin/trips/at-risk`: List trips with low occupancy nearing start dates.

## Bugs Identified & Fixes
- **Enum Comparison**: Resolved an issue where SQLAlchemy Enum objects were compared incorrectly against strings by standardizing on native Enum member comparison.
- **Circular Imports**: Fixed a recursive dependency between database base classes and models by refactoring metadata registration.
- **Startup Synchronization**: Implemented PostgreSQL healthchecks and deferrable table creation to ensure the application starts only after the database is ready for connections.

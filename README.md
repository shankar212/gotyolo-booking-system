# gotyolo-booking-system

## Project Overview
The gotyolo-booking-system is a high-concurrency backend service for the GoTyolo travel platform. It manages the complete lifecycle of trip bookings, including seat availability tracking, automated expiration of pending payments, financial refund calculations, and administrative performance metrics. The system is designed for high reliability and data consistency in a distributed environment.

## Tech Stack
- **FastAPI**: Chosen for its high performance, native support for asynchronous programming, and automatic OpenAPI documentation.
- **PostgreSQL**: Used as the primary relational database for its robust transaction support and advanced data integrity features.
- **SQLAlchemy**: Employed as the ORM to provide type-safe database interactions and complex aggregation capabilities.
- **APScheduler**: Manages background tasks, specifically the automated expiration of unpaid bookings.
- **Docker + Docker Compose**: Orchestrates the application and database services, ensuring environment consistency and simplified deployment.

## Engineering Design & Concurrency Strategy

### Booking Lifecycle & State Transitions
The booking system is modeled as a controlled state machine. Each booking moves through clearly defined states to ensure predictable behavior and prevent invalid transitions.

**Booking States**
- `PENDING_PAYMENT`: Initial state upon creation. Seats are reserved.
- `CONFIRMED`: Payment is successfully completed.
- `EXPIRED`: Payment failed or was not completed within the 15-minute window.
- `CANCELLED`: The booking is cancelled by the user.

**Valid Transitions**
- `PENDING_PAYMENT` → `CONFIRMED` (on payment success)
- `PENDING_PAYMENT` → `EXPIRED` (on payment failure or timeout)
- `CONFIRMED` → `CANCELLED` (user cancellation)
- `PENDING_PAYMENT` → `CANCELLED` (if allowed before confirmation)

All state transitions are validated at the service layer. Once a booking reaches `CANCELLED` or `EXPIRED`, it is in a terminal state and cannot transition further.

### Concurrency Strategy (Overbooking Prevention)
To prevent overbooking when multiple users attempt to book the last remaining seats simultaneously, the system employs database-level row locking.

During booking creation:
1. A database transaction is initiated.
2. The relevant trip row is fetched using `SELECT ... FOR UPDATE`.
3. Seat availability is verified.
4. If available:
    - The `available_seats` count is decremented.
    - A booking record is created in the `PENDING_PAYMENT` state.
5. The transaction is committed.

Pessimistic locking ensures that concurrent transactions must wait for the lock to be released, guaranteeing that seat counts never drop below zero.

### Database Transactions
Transactions are used to guarantee atomicity and consistency in all operations modifying seat inventory or booking states:

- **Booking Creation**: Atomic locking, validation, seat decrement, and record insertion.
- **Payment Webhook Processing**: Idempotency key validation, booking row locking, state update, and seat release on failure.
- **Cancellation**: Dual-locking (Booking and Trip), transition validation, refund calculation, and state update.
- **Auto-Expiry**: Atomic marking as `EXPIRED` and seat release.

### Auto-Expiry Mechanism
A lightweight background scheduler runs at fixed intervals (every minute) to keep the system state clean and metrics accurate.
- **Identification**: Selects bookings in `PENDING_PAYMENT` state where `expires_at` is in the past.
- **Execution**: Marks bookings as `EXPIRED` and releases reserved seats back to the trip inventory within a single transaction.

### Trade-offs & Design Decisions

#### Pessimistic vs. Optimistic Locking
Pessimistic row-level locking is chosen over optimistic strategies because seat allocation is highly contention-prone. This approach prioritizes correctness and simplifies recovery logic, avoiding complex retry mechanisms.

#### Denormalization Justification
The `Trip` model stores a denormalized `available_seats` field. This allows for constant-time availability checks and faster booking validation, avoiding expensive aggregation queries on the bookings table. Consistency is maintained by ensuring all seat updates occur within locked transactions, backed by a database constraint that prevents `available_seats` from becoming negative.

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

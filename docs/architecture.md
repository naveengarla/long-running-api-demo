# Architecture Overview

## High-Level Design

The "Long Running API Demo" implements the **Async Task Queue** pattern to handle operations that exceed standard HTTP timeouts. It decouples the **Request** (API) from the **Processing** (Worker) using a Message Broker (Redis) and a Database (PostgreSQL) for persistence.

```mermaid
graph TD
    Client[Client] -->|POST /tasks| API["FastAPI (Web Layer)"]
    Client -->|GET /tasks/:id| API
    Client -->|GET /tasks/:id/stream| API
    
    API -->|Push Task| Redis["Redis (Broker)"]
    API -->|Read/Write Job Status| DB[("PostgreSQL")]
    
    Worker["Celery Worker"] -->|Pop Task| Redis
    Worker -->|Update Status/Logs| DB
    Worker -->|GET (Scrape)| External["External Website"]
    
    API -.->|Trace| Jaeger["Jaeger (Tracing)"]
    Worker -.->|Trace| Jaeger
    External -.->|Trace (Client)| Jaeger
    
    subgraph "Data Layer"
        DB
    end

    subgraph "Observability"
        Jaeger
    end
    
    subgraph "Compute Layer"
        API
        Worker
    end
```

## Components

### 1. Web Layer (FastAPI)
*   **Role**: Entry point for all client requests.
*   **Responsibilities**:
    *   Input validation (Pydantic).
    *   Task submission to Celery.
    *   Persistence of Job metadata to PostgreSQL.
    *   Querying Job status and Logs.
    *   Real-time status streaming (SSE).
*   **Location**: `app/api/`, `app/main.py`

### 2. Worker Layer (Celery)
*   **Role**: Executes background tasks.
*   **Responsibilities**:
    *   Processing long-running logic (CPU/IO bound).
    *   **Web Scraping**: Fetching and parsing external websites (`requests` + `BeautifulSoup`).
    *   Updating Job status (RUNNING, SUCCESS, FAILED) in PostgreSQL.
    *   Writing granular progress logs to PostgreSQL.
    *   Handling retries and cancellations.
*   **Location**: `app/worker/`

### 3. Message Broker (Redis)
*   **Role**: Task queue and transport.
*   **Responsibilities**:
    *   Queuing tasks for workers.
    *   Storing ephemeral task state (Celery backend).

### 4. Persistence Layer (PostgreSQL)
*   **Role**: Durable storage for Jobs and Logs.
*   **Responsibilities**:
    *   Storing Job metadata (ID, Status, Inputs, Results).
    *   Storing audit logs and execution history.
    *   Ensuring data survives application restarts.
*   **Location**: Docker Container (`postgres:15-alpine`), `app/models/`
*   **Note**: We use **PostgreSQL** to support high concurrency and multiple worker replicas, avoiding the file-locking issues of SQLite.

### 5. Observability (OpenTelemetry & Jaeger)
*   **Role**: Distributed Tracing.
*   **Responsibilities**:
    *   Visualizing the full request lifecycle (`API -> Redis -> Worker -> DB`).
    *   Identifying performance bottlenecks and errors.
*   **Location**: Docker Container (`jaegertracing/all-in-one`), `app/core/telemetry.py`

## Modular Structure

The project follows a clean, modular architecture:

```text
app/
├── api/              # API Layer
│   ├── endpoints/    # Route handlers (Tasks)
│   └── router.py     # Main router configuration
├── core/             # Core Infrastructure
│   ├── config.py     # Environment settings
│   ├── database.py   # Database connection logic
│   └── celery_app.py # Celery app configuration
├── models/           # Data Models
│   └── job.py        # SQLAlchemy ORM models
├── schemas/          # Data Schemas
│   └── job.py        # Pydantic validation schemas
├── worker/           # Worker Layer
│   └── tasks.py      # Celery task implementations
└── main.py           # Application entry point
```

## Key Flows

### Job Submission
1.  Client POSTs to `/tasks`.
2.  API creates a `PENDING` Job record in SQLite.
3.  API pushes task to Redis via Celery.
4.  API returns `202 Accepted` with `task_id`.

### Job Processing
1.  Worker pops task from Redis.
2.  Worker updates Job status to `RUNNING` in SQLite.
3.  Worker executes logic, writing `JobLog` entries to SQLite.
4.  On completion, Worker updates status to `SUCCESS` or `FAILED`.

### Job Cancellation
1.  Client DELETEs `/tasks/{id}`.
2.  API revokes the Celery task (terminating the worker process).
3.  API updates Job status to `CANCELLED` in PostgreSQL.

### Web Scraper Flow
1.  Client submits `task_type: "web_scrape"` with URL.
2.  Worker fetches URL using `requests` (instrumented with OpenTelemetry).
3.  Worker parses HTML with `BeautifulSoup`.
4.  Worker extracts metadata (Title, H1s, Links).
5.  Worker updates DB with results.

## Reliability & Fault Tolerance

We have implemented specific patterns to ensure the system is resilient to crashes.

### 1. Late Acknowledgement (`acks_late`)
*   **Problem**: By default, Celery acknowledges (removes) a task from the queue *before* execution starts. If the worker crashes mid-task, the job is lost forever.
*   **Solution**: We enabled `task_acks_late=True`.
*   **Effect**: The task remains in Redis until the worker explicitly signals completion. If the connection drops, Redis re-queues the task for another worker.

### 2. Redis Persistence (AOF)
*   **Problem**: Redis is in-memory. If the Redis container restarts, all pending tasks are wiped out.
*   **Solution**: We enabled Append Only File (AOF) persistence (`--appendonly yes`).
*   **Effect**: Redis logs every write operation to disk. On restart, it replays these logs to restore the queue state.

### 3. Idempotency
*   **Problem**: With `acks_late`, a task might be delivered twice (e.g., worker finishes but crashes *before* sending the ACK).
*   **Solution**: The worker checks the Database status before starting.
*   **Effect**:
    ```python
    if job.status == "SUCCESS":
        return result  # Skip processing
    ```
    This ensures that re-running a task doesn't corrupt data or waste resources.

## FAQ: State Management

### 1. What if the client loses the Task ID?
*   **Scenario**: User closes the browser tab or clears cache.
*   **Recovery**: The client is **stateless**, but the server is **stateful**.
*   **Solution**: The client should call `GET /tasks` to fetch the history of all submitted jobs from the Database. In a real app, you would filter this by `user_id`.
*   **Takeaway**: Never rely solely on `localStorage`. Always allow fetching history from the server.

### 2. Source of Truth: DB vs. Celery vs. Flower
*   **Database (SQLite/Postgres)**: The **Ultimate Source of Truth**. It stores the permanent history, final results, and audit logs. Use this for `GET /tasks/{id}`.
*   **Redis (Celery Backend)**: The **Hot State**. It stores ephemeral progress updates (e.g., "10% done"). Use this for real-time streaming (`GET /tasks/{id}/stream`).
*   **Flower**: An **Admin Tool**. Use it for debugging and monitoring cluster health. **Never** build your application logic to depend on Flower's API.

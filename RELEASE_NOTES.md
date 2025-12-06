# Release Notes

## v0.0.7 - Feature: Web Scraper Task 🕷️

This release adds a real-world "Web Scraper" task to demonstrate practical long-running operations and external HTTP tracing.

### 🌟 New Features
*   **Web Scraper Task**: A new background task `scrape_website(url)` that fetches a URL, parses HTML with `BeautifulSoup`, and extracts metadata (Title, H1 count, Link count).
*   **Observability**: Added `opentelemetry-instrumentation-requests` to automatically trace external HTTP calls made by the worker. Use Jaeger to see the `GET <url>` span!
*   **UI Updates**: Added a Task Type selector (Vector vs. Scraper) and URL input to the frontend.

## v0.0.6 - Hotfix: Telemetry Stability 🚑

This hotfix disables `SQLAlchemyInstrumentor` to resolve a critical `greenlet` context error when used with the `asyncpg` driver in FastAPI.

### 🐛 Bug Fixes
*   **Fix 500 Internal Server Error**: Resolved `sqlalchemy.exc.MissingGreenlet` errors in the API by disabling automatic SQLAlchemy tracing. Request tracing (FastAPI) and Worker tracing (Celery) remain active and fully functional.

## v0.0.5 - Observability & Distributed Tracing 🕵️‍♂️

This release introduces full-stack observability using **OpenTelemetry** and **Jaeger**, allowing developers to visualize and trace requests as they flow through the system (API -> Redis -> Worker -> Database).

### 🌟 New Capabilities
*   **Distributed Tracing**: Integrated **Jaeger** (v1.53) to visualize request lifecycles.
*   **Instrumentation**: Added OpenTelemetry instrumentation for:
    *   **FastAPI**: Trace HTTP requests and latency.
    *   **Celery**: Trace background task execution and queuing time.
    *   **SQLAlchemy**: Trace database queries.
    *   **Redis**: Trace broker interactions.

### 🏗 Infrastructure
*   **Jaeger Service**: Added `jaeger` container to `docker-compose.yml`, exposing the UI on port **16686**.
*   **Telemetry Utility**: Added `app/core/telemetry.py` to simplify OTLP configuration.

## v0.0.4 - PostgreSQL Migration & Improved Stability 🐘

This major release transitions the application's persistence layer from SQLite to **PostgreSQL**, addressing critical scalability and concurrency limitations. It also includes significant stability improvements for Server-Sent Events (SSE) and schema validation.

### 🌟 New Capabilities
*   **Production-Grade Database**: Switched from SQLite to **PostgreSQL 15** running in Docker. This enables:
    *   **High Concurrency**: Multiple workers can now process tasks simultaneously without `database is locked` errors.
    *   **Row-Level Locking**: Improved data integrity during high-throughput operations.
    *   **Scalability**: The database is now decoupled from the application file system, allowing for independent scaling.

### 🐛 Critical Bug Fixes
*   **SSE Real-Time Updates**:
    *   **Fixed**: Resolved a critical issue where the UI progress bar remained stuck at 0%.
    *   **Root Cause**: Mismatch between Celery's auto-generated Task ID and the application's Database ID.
    *   **Resolution**: Enforced ID synchronization (`task_id=job.id`) and updated endpoints to use `celery_app.AsyncResult` for correct Redis backend lookups.
*   **API 500 Errors**:
    *   **Fixed**: Resolved `ResponseValidationError` when fetching task status.
    *   **Root Cause**: Pydantic schema field `task_id` did not match SQLAlchemy model field `id`.
    *   **Resolution**: Added `serialization_alias` to `TaskStatusResponse` and correctly mapped eager-loaded relationships.

### 🏗 Infrastructure & Developer Experience
*   **Unified Docker Stack**: Updated `docker-compose.yml` to orchestrate the entire platform (API, Worker, Redis, Postgres) with a single command: `docker-compose up -d`.
*   **Port Reconfiguration**:
    *   **API**: Moved to port **8001** (default) to prevent conflicts with other local services.
    *   **PostgreSQL**: Exposed on port **5433** to avoid clashes with local Postgres instances.
*   **Verification Scripts**: Added `verify_sse.py` and updated `verify_persistence.py` to support the new port configuration and end-to-end testing flows.

### 🔧 Internal Improvements
*   **Dependency Updates**: Added `asyncpg` (for high-performance async DB access) and `psycopg2-binary` (for robust synchronous Celery worker access).
*   **Configuration Management**: Centralized database connection strings in `app/core/config.py` to support both Sync and Async drivers easily.

## v0.0.3 - Technical Documentation Update

This release focuses on providing comprehensive technical guidance for architects, DevOps engineers, and developers implementing long-running operations.

### 📚 New Documentation
*   **[Infrastructure Sizing Guide](docs/aks_sizing_guide.md)**: Detailed calculations for sizing Azure AKS clusters, including Pod resources, Node Pools, and HPA/KEDA configurations.
*   **[Best Practices & Anti-Patterns](docs/best_practices.md)**: A guide on the "Claim Check" pattern for large payloads, idempotency, and common pitfalls to avoid.
*   **[Streaming Guide](docs/streaming_guide.md)**: Technical deep dive into Server-Sent Events (SSE) implementation.

### 🚀 Improvements
*   **README.md**: Enhanced with a clear "Problem Statement" explaining why long-running HTTP requests are an anti-pattern and how this solution addresses it.
*   **README.md**: Added a "Technical Guides" table for easier navigation.

# Release Notes

## v0.0.4 - PostgreSQL Migration & Stability
This release migrates the persistence layer to **PostgreSQL** to resolve concurrency and file-locking issues, ensuring a production-grade architecture.

### ⚡ Critical Improvements
*   **PostgreSQL Migration**: Replaced SQLite with PostgreSQL 15 (via Docker) to prevent `database is locked` errors during concurrent API/Worker access.
*   **SSE Reliability**: Fixed a mismatch between Celery Task IDs and Database IDs that prevented real-time progress updates.
*   **Dependencies**: Added `asyncpg` and `psycopg2-binary` drivers.

### 🛠 Configuration Changes
*   **Ports**: API moved to Port **8001** to avoid local conflicts. Postgres default port mapped to **5433**.
*   **Docker**: `docker-compose.yml` now orchestrates the full stack (API, Worker, Redis, Postgres).

## v0.0.3 - Technical Documentation Update

This release focuses on providing comprehensive technical guidance for architects, DevOps engineers, and developers implementing long-running operations.

### 📚 New Documentation
*   **[Infrastructure Sizing Guide](docs/aks_sizing_guide.md)**: Detailed calculations for sizing Azure AKS clusters, including Pod resources, Node Pools, and HPA/KEDA configurations.
*   **[Best Practices & Anti-Patterns](docs/best_practices.md)**: A guide on the "Claim Check" pattern for large payloads, idempotency, and common pitfalls to avoid.
*   **[Streaming Guide](docs/streaming_guide.md)**: Technical deep dive into Server-Sent Events (SSE) implementation.

### 🚀 Improvements
*   **README.md**: Enhanced with a clear "Problem Statement" explaining why long-running HTTP requests are an anti-pattern and how this solution addresses it.
*   **README.md**: Added a "Technical Guides" table for easier navigation.

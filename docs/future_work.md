# Future Work & Enhancements

This document outlines recommended improvements and "Day 2" operations features to take this reference implementation to a fully observable, resilient, and secure enterprise standard.

## 1. Observability (OpenTelemetry)
*   **Why**: Currently, the system relies on basic logs and the Flower dashboard. In a production distributed system, tracing a request from the API -> Redis -> Worker -> Database is crucial for debugging performance bottlenecks.
*   **Recommendation**: Integrate **OpenTelemetry** to auto-instrument FastAPI and Celery.
*   **Goal**: Send traces to a backend like Jaeger, Zipkin, or Azure Monitor to visualize the full request lifecycle.

## 2. Resilience Patterns (Circuit Breakers & Retries)
*   **Why**: Workers often depend on external APIs (e.g., OpenAI, Database) that may experience downtime. Uncontrolled retries can cascade failures.
*   **Recommendation**: Implement **Tenacity** for exponential backoff retries and a **Circuit Breaker** pattern (e.g., using `pybreaker`).
*   **Goal**: Build self-healing workers that fail fast when dependencies are down and recover automatically.

## 3. Dead Letter Queues (DLQ) & Handling Failures
*   **Why**: If a task fails repeatedly (e.g., due to malformed data), it shouldn't be lost or block the queue forever.
*   **Recommendation**: Configure a **Dead Letter Exchange** in Celery.
*   **Goal**: Automatically route failed tasks to a separate queue for manual inspection, replay, or discarding, ensuring zero data loss.

## 4. Security: Rate Limiting & Auth
*   **Why**: Long-running tasks are computationally expensive. A single user shouldn't be allowed to flood the queue and starve others.
*   **Recommendation**: Implement **Rate Limiting** (e.g., 10 tasks/min per user) using Redis and standard **API Key/JWT Authentication**.
*   **Goal**: Protect compute resources from abuse and ensure fair usage.

## 5. Infrastructure as Code (Helm Charts)
*   **Why**: `docker-compose` is excellent for local development, but production environments typically run on Kubernetes.
*   **Recommendation**: Create a **Helm Chart** for the entire stack (API, Worker, Redis).
*   **Goal**: Parameterize the sizing values (from the [AKS Sizing Guide](aks_sizing_guide.md)) to allow consistent, version-controlled deployments to Kubernetes.

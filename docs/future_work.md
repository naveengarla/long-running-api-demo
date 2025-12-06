# Future Work & Enhancements

This document outlines recommended improvements and "Day 2" operations features to take this reference implementation to a fully observable, resilient, and secure enterprise standard.

## 1. Observability (OpenTelemetry) ✅ **Implemented**
*   **Status**: Done. API and Worker natively trace requests to Jaeger. `requests` library is also instrumented.

## 2. Resilience Patterns (Circuit Breakers & Retries) ✅ **Implemented**
*   **Status**: Done. `Tenacity` handles retries, and `pybreaker` is used for the Circuit Breaker pattern in `app/worker.py`.

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

# Best Practices & Anti-Patterns for Long-Running Operations

This guide outlines critical architectural decisions, caveats, and industry-standard practices for building robust long-running API systems.

## 1. Data Handling: The Claim Check Pattern

### ⚠️ Caveat: Large Payloads in Redis
Redis is an in-memory store designed for speed, not storage capacity. Storing large payloads (e.g., > 1MB) directly in the Redis queue can lead to:
*   **OOM (Out of Memory)** errors.
*   **Network Saturation** during task serialization/deserialization.
*   **High Latency** for all operations on the Redis instance.

### ✅ Best Practice: Claim Check Pattern
Instead of sending the actual data through the queue, store the data in a blob store (like Azure Blob Storage or AWS S3) and pass only the **reference (URL/Path)** to the worker.

**Flow:**
1.  **API**: Uploads large payload to Blob Storage -> Gets `blob_url`.
2.  **API**: Enqueues task with `blob_url` as an argument.
3.  **Worker**: Dequeues task -> Downloads data from `blob_url` -> Processes it.

```python
# BAD: Passing large data directly
process_vector_data.delay(large_json_object)

# GOOD: Passing a reference
blob_url = upload_to_blob(large_json_object)
process_vector_data.delay(blob_url)
```

## 2. Reliability & Resilience

### ✅ Best Practice: Idempotency
Workers can crash or be restarted (e.g., Spot instance preemption). The queue mechanism might redeliver the same message.
*   **Rule**: Ensure your task logic is **idempotent**. Running the same task twice should not corrupt data or duplicate results.
*   **Implementation**: Check if the work is already done (e.g., by checking a database record status) before starting processing.

### ✅ Best Practice: Graceful Shutdowns
Configure your workers to handle `SIGTERM` signals. When a node scales down, the worker should stop accepting new tasks and finish the current one within a grace period (e.g., 60s).

## 3. Timeouts & Latency

### ⚠️ Caveat: Gateway Timeouts
Load Balancers (Azure App Gateway, Nginx) often have a default idle timeout (e.g., 60s or 120s).
*   **Issue**: If a client is waiting for a response (polling or SSE) and the connection is idle, the gateway might kill it.
*   **Fix**:
# Best Practices & Anti-Patterns for Long-Running Operations

This guide outlines critical architectural decisions, caveats, and industry-standard practices for building robust long-running API systems.

## 1. Data Handling: The Claim Check Pattern

### ⚠️ Caveat: Large Payloads in Redis
Redis is an in-memory store designed for speed, not storage capacity. Storing large payloads (e.g., > 1MB) directly in the Redis queue can lead to:
*   **OOM (Out of Memory)** errors.
*   **Network Saturation** during task serialization/deserialization.
*   **High Latency** for all operations on the Redis instance.

### ✅ Best Practice: Claim Check Pattern
Instead of sending the actual data through the queue, store the data in a blob store (like Azure Blob Storage or AWS S3) and pass only the **reference (URL/Path)** to the worker.

**Flow:**
1.  **API**: Uploads large payload to Blob Storage -> Gets `blob_url`.
2.  **API**: Enqueues task with `blob_url` as an argument.
3.  **Worker**: Dequeues task -> Downloads data from `blob_url` -> Processes it.

```python
# BAD: Passing large data directly
process_vector_data.delay(large_json_object)

# GOOD: Passing a reference
blob_url = upload_to_blob(large_json_object)
process_vector_data.delay(blob_url)
```

## 2. Reliability & Resilience

### ✅ Best Practice: Idempotency
Workers can crash or be restarted (e.g., Spot instance preemption). The queue mechanism might redeliver the same message.
*   **Rule**: Ensure your task logic is **idempotent**. Running the same task twice should not corrupt data or duplicate results.
*   **Implementation**: Check if the work is already done (e.g., by checking a database record status) before starting processing.

### ✅ Best Practice: Graceful Shutdowns
Configure your workers to handle `SIGTERM` signals. When a node scales down, the worker should stop accepting new tasks and finish the current one within a grace period (e.g., 60s).

## 3. Timeouts & Latency

### ⚠️ Caveat: Gateway Timeouts
Load Balancers (Azure App Gateway, Nginx) often have a default idle timeout (e.g., 60s or 120s).
*   **Issue**: If a client is waiting for a response (polling or SSE) and the connection is idle, the gateway might kill it.
*   **Fix**:
    *   **SSE**: Send "heartbeat" comments (`: ping\n\n`) every 15-30 seconds to keep the connection alive.
    *   **Polling**: Ensure the API returns immediately with the current status, never block for long periods.

### 4. Persistence & Audit Trails
- **Practice**: Store job metadata and logs in a durable database (e.g., PostgreSQL, SQLite).
- **Why**: 
    - **Auditability**: You need to know who ran what and when.
    - **Debugging**: Granular logs stored per-job help debug failures without grepping through massive server logs.
    - **Recovery**: If the Redis broker crashes, the DB record remains as the source of truth.
- **Implementation**:
    - Create a `Job` table with `status`, `input`, `result`, and timestamps.
    - Create a `JobLog` table linked to the `Job` for detailed execution steps.

## 5. Common Anti-Patterns
- **Database as Queue**: Don't use a SQL table as a queue (polling for "PENDING" rows). It locks rows and doesn't scale. Use a real broker like Redis or RabbitMQ.
- **Fire and Forget**: Always track the task ID. If you don't, you can't cancel it or know if it failed.
- **Synchronous Waiting**: Never use `task.get()` inside an API request handler. It blocks the thread and defeats the purpose of async workers.
- **Monolithic Worker**: If you have different types of tasks (e.g., CPU-heavy vs IO-heavy), use separate queues and worker pools to prevent one type from starving the other.

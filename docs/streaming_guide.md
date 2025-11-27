# Real-Time Task Streaming with Server-Sent Events (SSE)

This guide details the technical implementation of real-time task progress streaming in our FastAPI application. We use **Server-Sent Events (SSE)** to push updates from the server to the client, providing a more efficient and responsive experience compared to traditional polling.

## Foundational Concepts

### What is SSE?
Server-Sent Events (SSE) is a standard allowing servers to push data to web pages over a single, long-lived HTTP connection. Unlike WebSockets, which are bidirectional, SSE is **unidirectional** (Server -> Client), making it perfect for status updates, news feeds, or progress bars where the client doesn't need to send data back over the same channel.

### SSE vs. Polling vs. WebSockets

| Feature | Short Polling | Server-Sent Events (SSE) | WebSockets |
| :--- | :--- | :--- | :--- |
| **Direction** | Client pulls | Server pushes | Bidirectional |
| **Connection** | New request every X sec | Single long-lived HTTP | Single long-lived TCP |
| **Efficiency** | Low (header overhead) | High (text stream) | High (binary/text) |
| **Complexity** | Low | Medium | High |
| **Use Case** | Rare updates | Progress, Feeds, Logs | Chat, Games, Trading |

For our use case (task progress), SSE is the **ideal choice** because:
1.  We only need one-way updates (Server -> Client).
2.  It works over standard HTTP/HTTPS (no special proxy config needed).
3.  It has native browser support via the `EventSource` API.

---

## Backend Implementation (FastAPI)

We use FastAPI's `StreamingResponse` to keep the HTTP connection open and yield data chunks.

### The Generator Pattern
Instead of returning a single JSON object, we define an asynchronous generator function. This function loops, checks the task status, and `yields` formatted strings.

```python
# app/main.py

@app.get("/tasks/{task_id}/stream")
async def stream_task_status(task_id: str):
    async def event_generator():
        while True:
            # 1. Fetch status from Celery/Redis
            task_result = AsyncResult(task_id)
            
            # 2. Construct data payload
            data = {
                "task_id": task_id,
                "status": task_result.status,
                "result": task_result.result if task_result.status in ['PROGRESS', 'SUCCESS'] else None
            }
            
            # 3. Yield SSE formatted message
            # Format: "data: <json_string>\n\n"
            yield f"data: {json.dumps(data)}\n\n"

            # 4. Stop condition
            if task_result.ready():
                break
            
            # 5. Control update rate
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Key Technical Details:**
*   **`text/event-stream`**: The required Content-Type header for SSE.
*   **`data: ...\n\n`**: The specific wire format. Each message must start with `data:` and end with double newlines.
*   **`asyncio.sleep(1)`**: Prevents a tight loop, effectively throttling updates to 1 per second without closing the connection.

---

## Frontend Implementation (HTML/JS)

The browser uses the native `EventSource` API to consume the stream.

### The `EventSource` API
This API handles the connection management automatically. If the connection drops, it even attempts to reconnect (though we close it manually on completion).

```javascript
// app/static/index.html

function streamStatus(taskId) {
    // 1. Open Connection
    const eventSource = new EventSource(`/tasks/${taskId}/stream`);
    
    // 2. Handle Incoming Messages
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // Update UI (Progress Bar, Badges, etc.)
        updateProgressBar(data);

        // 3. Close Connection on Completion
        if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
            eventSource.close();
        }
    };

    // 4. Handle Errors
    eventSource.onerror = function(err) {
        console.error("Stream failed:", err);
        eventSource.close();
    };
}
```

**Key Technical Details:**
*   **`new EventSource(url)`**: Initiates the GET request with `Accept: text/event-stream`.
*   **`onmessage`**: Fires every time the server yields a `data: ...\n\n` block.
*   **`event.data`**: Contains the string payload sent by the server.
*   **`eventSource.close()`**: Crucial to stop the browser from keeping the connection open or reconnecting after the task is done.

## References
*   [MDN Web Docs: Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
*   [FastAPI Documentation: StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
*   [Celery Documentation: Task States](https://docs.celeryq.dev/en/stable/userguide/tasks.html#states)

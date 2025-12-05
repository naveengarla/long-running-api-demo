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

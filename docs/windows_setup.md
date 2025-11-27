# Windows 11 Local Setup Guide

Running distributed systems like Celery and Redis on Windows requires specific configurations, as these tools are primarily designed for Linux environments.

## Option 1: Docker Desktop (Recommended)

The industry-standard way to develop on Windows 11 is using **Docker Desktop with the WSL 2 backend**. This gives you a real Linux kernel, ensuring your local environment matches production.

1.  **Install Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/).
2.  **Enable WSL 2**: Docker Desktop will prompt you to enable WSL 2 during installation.
3.  **Run the Project**:
    ```powershell
    docker-compose up --build
    ```
    This works out-of-the-box without any code changes.

---

## Option 2: Native Windows (Without Docker)

If you cannot use Docker, you must apply specific workarounds.

### 1. Redis on Windows
Redis does not officially support Windows.
- **Solution A (WSL)**: Install Redis inside a WSL Ubuntu terminal: `sudo apt-get install redis-server`.
- **Solution B (Memurai)**: Use [Memurai](https://www.memurai.com/), a Redis-compatible cache for Windows.

### 2. Celery on Windows
Celery's default execution pool (`prefork`) does **not** work on Windows. You will see errors about "spawn" or the worker will hang.

**Workaround**: You must run the worker with the `solo` or `threads` pool.

#### Steps to Run Manually:

1.  **Start Redis** (via WSL or Memurai) on port `6379`.
2.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    ```
3.  **Start FastAPI** (Terminal 1):
    ```powershell
    uvicorn app.main:app --reload
    ```
4.  **Start Celery Worker** (Terminal 2):
    > [!IMPORTANT]
    > Note the `--pool=solo` flag. This is required for Windows.
    ```powershell
    celery -A app.worker.celery worker --loglevel=info --pool=solo
    ```

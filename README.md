# Long Running API Demo

A production-ready reference implementation for handling long-running operations in FastAPI using Celery and Redis.

## Overview

This project demonstrates the **Asynchronous Task Queue** pattern, which is the industry standard for handling heavy computations (like Vector DB indexing, image processing, or report generation) without blocking the HTTP client.

## Key Features

- **FastAPI**: Modern, high-performance web framework.
- **Celery**: Distributed task queue for background processing.
- **Redis**: In-memory message broker and result backend.
- **Flower**: Real-time monitoring dashboard for Celery.
- **HTML UI**: Built-in frontend with progress bars and history.
- **Docker Compose**: One-command setup for the entire stack.
- **Best Practices**: Includes retry logic, pydantic validation, and modular structure.

## Quick Start

1.  **Prerequisites**: Ensure you have Docker and Docker Compose installed.
2.  **Run the Stack**:
    ```bash
    docker-compose up --build
    ```
3.  **Access the App**: 
    - **UI**: [http://localhost:8000](http://localhost:8000)
    - **Monitoring**: [http://localhost:5555](http://localhost:5555)
    - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Architecture & Best Practices](docs/architecture.md): Deep dive into the design patterns, constraints, and trade-offs.
- [Windows 11 Setup Guide](docs/windows_setup.md): Specific instructions for running locally on Windows.
- [API Documentation](docs/architecture.md#5-api-documentation): Details on the endpoints.

## Project Structure

```
.
├── app/
│   ├── main.py       # FastAPI application & endpoints
│   ├── worker.py     # Celery worker & task definitions
│   └── models.py     # Pydantic data models
├── docs/             # Detailed documentation
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── verify_flow.py    # Script to verify the end-to-end flow
```

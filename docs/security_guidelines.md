# Security Guidelines & Best Practices 🔒

This document outlines the security considerations and best practices for deploying the Long-Running API Demo in an enterprise environment.

## 1. Authentication & Authorization

### 🚧 Current State
The reference implementation is currently **open** (no auth) for ease of demonstration.

### ✅ Best Practice: OAuth2 & OIDC
For production, **never** allow unauthenticated access to the API.

*   **Authentication**: Integrate with an Identity Provider (IdP) like Azure Entra ID (active Directory), Auth0, or AWS Cognito using **OpenID Connect (OIDC)**.
*   **Authorization**: Implement **Role-Based Access Control (RBAC)**.
    *   `Admin`: Can cancel tasks, view all jobs.
    *   `User`: Can only submit tasks and view *their own* jobs.
*   **Implementation**: Use `fastapi-azure-auth` or `python-jose` to validate JWT Bearer tokens in the `Dependency` layer.

## 2. Secrets Management

### ✅ Best Practice: Externalize Secrets
**Never** commit secrets (API keys, DB passwords) to source control.

*   **Development**: Use `.env` files (added to `.gitignore`).
*   **Production**: Inject secrets as environment variables from a secure vault:
    *   **Kubernetes**: Use Kubernetes Secrets or Azure Key Vault Provider for Secrets Store CSI Driver.
    *   **Docker**: Use `docker secret`.

## 3. Network Security

### ✅ Best Practice: Isolation & TLS
*   **VNET Injection**: Deploy the API, Worker, Redis, and Postgres services within a private Virtual Network (VNET) or VPC.
*   **TLS/SSL**: Terminate SSL at the Ingress Controller (e.g., Nginx, Azure App Gateway). Internal traffic should also be encrypted if required by compliance (mTLS).
*   **Redis**: In this demo, Redis runs receiving connections from any IP. In production:
    *   Bind Redis to the internal network interface only.
    *   **Enable Password Authentication**: Set `requirepass` in `redis.conf` and configure the `CELERY_BROKER_URL` with the password.
    *   **Disable Dangerous Commands**: Rename or disable commands like `FLUSHALL` or `CONFIG`.

## 4. Celery Worker Security

### ✅ Best Practice: Serialization & Execution
*   **Serialization**: We explicitly use `json` serialization (`task_serializer="json"` in `celery_app.py`). **Never use `pickle`**, as it allows arbitrary code execution if an attacker can inject a message into Redis.
*   **Root Privileges**: Run the Celery worker as a **non-root user** in the Docker container (configurable in `Dockerfile`).

## 5. Input Validation

### ✅ Best Practice: Pydantic
We use Pydantic models (e.g., `TaskCreate`) to strictly validate all incoming data.
*   **Sanitization**: Ensure string inputs (like URLs for the scraper) are validated to prevent SSRF (Server-Side Request Forgery) attacks.
*   **Allowlisting**: For the scraper, maintain an allowlist of permitted domains if possible, or block internal IP ranges (e.g., `169.254.169.254` for cloud metadata services).

## 6. Dependency Management

### ✅ Best Practice: Vulnerability Scanning
*   **Container Scanning**: Integrate tools like Trivy or Snyk into your CI/CD pipeline to scan `postgres`, `redis`, and your custom images for CVEs.
*   **Python Dependencies**: Regularly run `pip-audit` or Dependabot to update libraries with known vulnerabilities.

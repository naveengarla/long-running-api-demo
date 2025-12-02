# Azure AKS Infrastructure Sizing Guide

This document outlines the infrastructure sizing calculations and configuration recommendations for hosting the Long Running API application on Azure Kubernetes Service (AKS).

## 1. Architecture Overview

The application consists of three main components:
*   **Web API (FastAPI)**: Handles HTTP requests, submits tasks to the queue, and provides status updates. Stateless and CPU-bound during request handling.
*   **Worker (Celery)**: Processes background tasks. CPU and Memory intensive depending on the workload (vector processing).
*   **Message Broker (Redis)**: Manages the task queue and stores task results.

## 2. Sizing Assumptions

To demonstrate the sizing calculations, we assume the following baseline load profile. **These values should be adjusted based on actual load testing results.**

*   **Peak API Request Rate**: 100 requests per second (RPS).
*   **Peak Concurrent Tasks**: 1,000 tasks in the queue/processing.
*   **Average Task Duration**: 30 seconds.
*   **Task Resource Profile (Estimated)**:
    *   0.5 vCPU
    *   512 MiB Memory

## 3. Component Sizing & Configuration

### 3.1 Web API (Stateless)

The Web API is primarily I/O bound (waiting for Redis) but requires CPU for request parsing and serialization.

*   **Pod Sizing**:
    *   **Requests**: 250m CPU, 256Mi Memory
    *   **Limits**: 500m CPU, 512Mi Memory
*   **Scalability (HPA)**:
    *   Use **Horizontal Pod Autoscaler (HPA)** based on CPU utilization.
    *   **Target CPU**: 70%
    *   **Min Replicas**: 3 (for high availability)
    *   **Max Replicas**: Calculated as `(Peak RPS / RPS per Pod) * Buffer`.
        *   *Assumption*: 1 Pod can handle 20 RPS.
        *   *Calculation*: `(100 / 20) * 1.5 (buffer) = 7.5` -> **8 Replicas**.

### 3.2 Worker (Background Processing)

The Worker is the heavy lifter. Sizing is directly proportional to the number of concurrent tasks and the desired processing latency.

*   **Pod Sizing**:
    *   **Requests**: 500m CPU, 512Mi Memory (Matches task profile to ensure 1:1 mapping or predictable packing)
    *   **Limits**: 1000m CPU, 1Gi Memory (Allow bursting for short spikes)
*   **Scalability (KEDA)**:
    *   Use **KEDA (Kubernetes Event-driven Autoscaling)** to scale based on Redis queue length.
    *   **Trigger**: `redis` scaler.
    *   **Target Queue Length**: 5 (Scale up if more than 5 tasks are waiting per pod).
    *   **Max Replicas**: Calculated as `Peak Concurrent Tasks / Target Queue Length`.
        *   *Calculation*: `1000 / 5 = 200` -> **200 Replicas** (This is a theoretical max; practically limited by node pool size).

### 3.3 Redis (Broker & Backend)

*   **Service**: Azure Cache for Redis.
*   **Tier**: **Standard C1** (1 GB, up to 1,000 client connections) is a good starting point.
*   **Upgrade Trigger**: If memory usage > 70% or if CPU load on Redis instance is high due to high connection churn. For production with high reliability requirements, consider **Premium P1** for persistence and better network performance.

## 4. Infrastructure Sizing (AKS Cluster)

### 4.1 Node Pools

We recommend separating system components from application workloads.

#### System Node Pool
*   **Purpose**: Runs CoreDNS, metrics-server, KEDA operator, ingress controllers, etc.
*   **VM Size**: **Standard_DS2_v2** (2 vCPU, 7 GB RAM).
*   **Count**: 2-3 nodes (Fixed).

#### User Node Pool (Application Workload)
*   **Purpose**: Runs Web API and Worker pods.
*   **VM Size**: **Standard_D4s_v5** (4 vCPU, 16 GB RAM).
    *   *Rationale*: Good balance of CPU/Memory for general compute.
*   **Capacity Calculation**:
    *   **Allocatable Resources per Node**: ~3.8 vCPU, ~14 GB RAM (after OS/Kubelet overhead).
    *   **Web API Demand**: 8 Replicas * 0.25 CPU = 2 vCPU.
    *   **Worker Demand**: 200 Replicas * 0.5 CPU = 100 vCPU.
    *   **Total CPU Needed**: 102 vCPU.
    *   **Nodes Needed**: `102 / 3.8` ≈ 27 Nodes.
*   **Cluster Autoscaler**:
    *   **Min Nodes**: 2 (Cost saving during low load).
    *   **Max Nodes**: 30 (To handle peak load + buffer).

## 5. Summary of Configuration

| Component | Resource Requests | Resource Limits | Scaling Metric | Scale Target |
| :--- | :--- | :--- | :--- | :--- |
| **Web API** | 250m CPU, 256Mi Mem | 500m CPU, 512Mi Mem | CPU Utilization | 70% |
| **Worker** | 500m CPU, 512Mi Mem | 1000m CPU, 1Gi Mem | Redis List Length | 5 items |
| **Redis** | N/A (PaaS) | N/A (PaaS) | Memory/Connections | N/A |
| **AKS Nodes**| N/A | N/A | Pending Pods | N/A |

## 6. Scalability & Reliability Considerations

To ensure the system is robust and can handle varying loads, consider the following scalability mechanisms and reliability best practices for each layer.

| Layer | Scalability Point | Scalability Mechanism | Reliability & Config Considerations |
| :--- | :--- | :--- | :--- |
| **Ingress** | Ingress Controller / Load Balancer | **Azure App Gateway / Load Balancer**: Auto-scales based on traffic. | • Enable **WAF** for security.<br>• Use **Multi-zone** deployment for high availability.<br>• Configure proper **timeouts** for long-running connections (if using SSE). |
| **Web API** | FastAPI Pods | **HPA (Horizontal Pod Autoscaler)**: Scales based on CPU/Memory usage. | • **Readiness Probes**: Ensure traffic only goes to healthy pods.<br>• **Pod Anti-Affinity**: Spread pods across different nodes/zones.<br>• **Pod Disruption Budget (PDB)**: Ensure min available replicas during upgrades. |
| **Queue** | Redis | **Vertical Scaling**: Upgrade tier (C1 -> P1).<br>**Clustering**: Shard data (advanced). | • **Persistence**: Enable RDB/AOF backups (Premium tier).<br>• **Replicas**: Use primary-replica architecture for failover.<br>• **Connection Pooling**: Use connection pools in app to avoid exhaustion. |
| **Worker** | Celery Workers | **KEDA**: Scales based on Redis List length (queue depth). | • **Graceful Shutdown**: Handle `SIGTERM` to finish active tasks before stopping.<br>• **Idempotency**: Ensure tasks can be safely retried if interrupted.<br>• **Dead Letter Queue**: Handle failed tasks to prevent blocking. |
| **Compute** | AKS Nodes | **Cluster Autoscaler**: Adds/removes nodes based on pending pods. | • **System Node Pool**: Isolate system pods from app workloads.<br>• **Spot Instances**: Use for workers (with retry logic) to save costs.<br>• **Over-provisioning**: Keep a small buffer of spare nodes for faster scale-up. |

## 7. Cost Optimization Tips
*   **Spot Instances**: Use Spot instances for the Worker node pool since Celery tasks can be retried if a node is preempted. This can save up to 90% on compute costs.
*   **Auto-shutdown**: For non-production environments, schedule cluster shutdown during off-hours.

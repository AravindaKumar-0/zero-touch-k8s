# Containerized Frontend-Backend App — CI/CD to Kubernetes (K3s)

End-to-end CI/CD pipeline that builds, versions, and deploys a two-tier
(frontend + backend) application to a Kubernetes (K3s) cluster using
Jenkins, Docker, and Helm — with automated rollout verification and
health checks.

## Architecture

<img width="1265" height="833" alt="k8s-architecture" src="https://github.com/user-attachments/assets/c13e4a3d-96c3-4930-aaad-68f114c10058" />

GitHub Repo (source + Dockerfiles + Helm chart)
│ (GitHub webhook trigger on push to main)
▼
Jenkins Pipeline
│
├─ Checkout source
├─ Build Docker images (frontend, backend)
├─ Tag images with Jenkins BUILD_NUMBER
├─ Push images to Docker Hub
├─ helm upgrade --install (kubeconfig credential)
├─ Verify rollout status (kubectl rollout status)
├─ Auto-rollback on failed rollout (kubectl rollout undo)
├─ Check Pods / Services are healthy
└─ Backend API health check (curl/HTTP probe)
▼
K3s Cluster
├─ Frontend Deployment + Service → exposed via Traefik Ingress
└─ Backend Deployment + Service → internal ClusterIP


## Tech Stack

| Layer               | Tool/Tech                                |
| ------------------- | ----------------------------------------- |
| Source control      | GitHub                                   |
| CI/CD orchestration | Jenkins (declarative pipeline)           |
| Containerization    | Docker                                   |
| Image registry      | Docker Hub                               |
| Orchestration       | Kubernetes (K3s)                         |
| Deployment tooling  | Helm 3                                   |
| Ingress/routing     | Traefik                                  |
| Cluster access      | Jenkins Kubernetes/kubeconfig credential |

## Repository Structure

.
├── frontend/
│ ├── Dockerfile
│ └── src/
├── backend/
│ ├── Dockerfile
│ └── src/
├── helm/
│ └── app-chart/
│ ├── Chart.yaml
│ ├── values.yaml
│ └── templates/
│ ├── frontend-deployment.yaml
│ ├── frontend-service.yaml
│ ├── backend-deployment.yaml
│ ├── backend-service.yaml
│ └── ingress.yaml
├── Jenkinsfile
└── README.md


## Pipeline Stages (Jenkinsfile)

1. **Checkout** — pulls latest source from GitHub
2. **Build** — builds separate Docker images for frontend and backend
3. **Tag & Push** — tags images with `${BUILD_NUMBER}` and pushes to Docker Hub
4. **Deploy** — runs `helm upgrade --install` against the K3s cluster using a Jenkins-stored kubeconfig credential, pinning the exact image tags built in this run
5. **Verify Rollout** — `kubectl rollout status` on both deployments; fails the pipeline on rollout failure
6. **Auto-Rollback** — if rollout verification fails (bad image, crash loop, failed probe), the pipeline automatically runs `kubectl rollout undo` on both deployments and fails the build loudly instead of leaving a broken release running
7. **Post-deploy Health Check** — hits the backend `/health` (or equivalent) endpoint to confirm the API is serving traffic

## Reliability

- **Resource requests/limits** set on both frontend and backend containers to prevent noisy-neighbor resource contention on the K3s node.
- **Liveness probes** restart a container if the app hangs or deadlocks.
- **Readiness probes** ensure Kubernetes only routes traffic to pods that have passed their health check, avoiding requests hitting a pod still starting up.

## Trigger

Pipeline runs automatically on every push to `main` via a GitHub webhook configured against the Jenkins job (`/github-webhook/` endpoint). Manual trigger via "Build Now" is still available for testing.

## Prerequisites

- K3s cluster (single or multi-node)
- Jenkins with Docker, `kubectl`, and `helm` available on the agent
- Jenkins credentials configured:
  - Docker Hub username/password (or token)
  - Kubeconfig for the target cluster
- Traefik installed on the cluster (default with K3s)
- GitHub webhook configured against the Jenkins job for automatic triggering

## Setup / Run Locally

```bash
# 1. Clone
git clone https://github.com/<your-username>/<repo-name>.git

# 2. Build images manually (optional, for local testing)
docker build -t <dockerhub-user>/frontend:local ./frontend
docker build -t <dockerhub-user>/backend:local ./backend

# 3. Deploy via Helm
helm upgrade --install app-release ./helm/app-chart \
  --set frontend.image.tag=local \
  --set backend.image.tag=local

# 4. Verify
kubectl get pods
kubectl get svc
kubectl get ingress
```

The full pipeline triggers automatically on push to `main` (see Trigger section above). Manual trigger via Jenkins "Build Now" remains available for local testing.

## Key Design Decisions

- **Immutable image tags** (`BUILD_NUMBER`) instead of `latest`, so every deployment is traceable back to an exact Jenkins build and Git commit.
- **Helm over raw manifests** for parameterized, repeatable deploys across environments.
- **Rollout verification as a pipeline gate** — the pipeline fails loudly if `kubectl rollout status` doesn't succeed, instead of reporting false-green.
- **Auto-rollback on failure** — a bad deploy self-heals to the last known-good release instead of requiring manual intervention.

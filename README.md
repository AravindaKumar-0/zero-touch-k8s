# Containerized Frontend-Backend App — CI/CD to Kubernetes (K3s)

End-to-end CI/CD pipeline that builds, versions, and deploys a two-tier
(frontend + backend) application to a Kubernetes (K3s) cluster using
Jenkins, Docker, and Helm — with automated rollout verification and
health checks.

## Architecture

```
GitHub Repo (source + Dockerfiles + Helm chart)
        │  (manual/webhook trigger)
        ▼
   Jenkins Pipeline
        │
        ├─ Checkout source
        ├─ Build Docker images (frontend, backend)
        ├─ Tag images with Jenkins BUILD_NUMBER
        ├─ Push images to Docker Hub
        ├─ helm upgrade --install (kubeconfig credential)
        ├─ Verify rollout status (kubectl rollout status)
        ├─ Check Pods / Services are healthy
        └─ Backend API health check (curl/HTTP probe)
        ▼
   K3s Cluster
        ├─ Frontend Deployment + Service  → exposed via Traefik Ingress
        └─ Backend Deployment + Service   → internal ClusterIP
```

## Tech Stack

| Layer            | Tool/Tech                          |
|-------------------|-------------------------------------|
| Source control     | GitHub                              |
| CI/CD orchestration | Jenkins (declarative pipeline)     |
| Containerization   | Docker                              |
| Image registry     | Docker Hub                          |
| Orchestration      | Kubernetes (K3s)                    |
| Deployment tooling  | Helm 3                              |
| Ingress/routing    | Traefik                             |
| Cluster access      | Jenkins Kubernetes/kubeconfig credential |

## Repository Structure

```
.
├── frontend/
│   ├── Dockerfile
│   └── src/
├── backend/
│   ├── Dockerfile
│   └── src/
├── helm/
│   └── app-chart/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── frontend-deployment.yaml
│           ├── frontend-service.yaml
│           ├── backend-deployment.yaml
│           ├── backend-service.yaml
│           └── ingress.yaml
├── Jenkinsfile
└── README.md
```

## Pipeline Stages (Jenkinsfile)

1. **Checkout** — pulls latest source from GitHub
2. **Build** — builds separate Docker images for frontend and backend
3. **Tag & Push** — tags images with `${BUILD_NUMBER}` and pushes to Docker Hub
4. **Deploy** — runs `helm upgrade --install` against the K3s cluster using a Jenkins-stored kubeconfig credential, pinning the exact image tags built in this run
5. **Verify Rollout** — `kubectl rollout status` on both deployments; fails the pipeline on rollout failure
6. **Post-deploy Health Check** — hits the backend `/health` (or equivalent) endpoint to confirm the API is serving traffic

## Prerequisites

- K3s cluster (single or multi-node)
- Jenkins with Docker, `kubectl`, and `helm` available on the agent
- Jenkins credentials configured:
  - Docker Hub username/password (or token)
  - Kubeconfig for the target cluster
- Traefik installed on the cluster (default with K3s)

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

Trigger the full pipeline by running the Jenkins job (manual trigger currently;
webhook-based auto-trigger is a planned enhancement — see below).

## Key Design Decisions

- **Immutable image tags** (`BUILD_NUMBER`) instead of `latest`, so every
  deployment is traceable back to an exact Jenkins build and Git commit.
- **Helm over raw manifests** for parameterized, repeatable deploys across
  environments.
- **Rollout verification as a pipeline gate** — the pipeline fails loudly if
  `kubectl rollout status` doesn't succeed, instead of reporting false-green.

# DevOpsDojo Kubernetes Operator

A Kubernetes Operator built with [Kopf](https://kopf.readthedocs.io/) that manages the complete lifecycle of the DevOpsDojo application.

## Features

- **Lifecycle Orchestration**: Ensures proper startup order
  1. PostgreSQL StatefulSet starts first
  2. Database migration job runs after DB is ready
  3. Backend deployment starts after migration completes
  4. Frontend deployment starts after backend is ready

- **Self-healing**: Continuously monitors and reconciles state
- **Status Tracking**: Real-time status updates on CR
- **Automatic Cleanup**: Owner references handle cascade deletion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DevOpsDojo CRD                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ spec:                                                 │  │
│  │   database: { storage, resources }                    │  │
│  │   backend:  { replicas, image, resources }            │  │
│  │   frontend: { replicas, image, resources }            │  │
│  │   ingress:  { enabled, host, annotations }            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Kopf Operator Controller                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Create  │───▶│ Timer   │───▶│ Update  │───▶│ Delete  │  │
│  │ Handler │    │ Handler │    │ Handler │    │ Handler │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     ┌────────────┐    ┌────────────┐    ┌────────────┐
     │ PostgreSQL │    │  Backend   │    │  Frontend  │
     │ StatefulSet│───▶│ Deployment │───▶│ Deployment │
     └────────────┘    └────────────┘    └────────────┘
            │                 ▲
            ▼                 │
     ┌────────────┐           │
     │ Migration  │───────────┘
     │    Job     │
     └────────────┘
```

## Lifecycle Phases

| Phase | Description |
|-------|-------------|
| `Pending` | CR created, starting deployment |
| `CreatingDatabase` | Creating PostgreSQL StatefulSet |
| `WaitingForDatabase` | Waiting for PostgreSQL to be ready |
| `RunningMigration` | Running database migration job |
| `WaitingForMigration` | Waiting for migration to complete |
| `DeployingBackend` | Deploying backend pods |
| `DeployingFrontend` | Deploying frontend pods |
| `Ready` | All components deployed and healthy |
| `Failed` | Deployment failed (check message) |

## Installation

### 1. Build and Push Operator Image

```bash
# Build the image
docker build -t <your-registry>/devopsdojo-operator:latest ./operator

# Push to registry
docker push <your-registry>/devopsdojo-operator:latest
```

### 2. Update Image Reference

```bash
# Update the image in deployment manifest
sed -i 's|devopsdojo-operator:latest|<your-registry>/devopsdojo-operator:latest|g' \
  operator/manifests/operator-deployment.yaml
```

### 3. Deploy the Operator

```bash
# Install CRD
kubectl apply -f operator/manifests/crd.yaml

# Install RBAC
kubectl apply -f operator/manifests/rbac.yaml

# Deploy operator
kubectl apply -f operator/manifests/operator-deployment.yaml
```

### Quick Install (All-in-one)

```bash
./operator/install.sh
```

## Usage

### Create a DevOpsDojo Instance

```bash
# Create namespace and secrets first
kubectl apply -f operator/examples/secrets.yaml

# Deploy DevOpsDojo (dev)
kubectl apply -f operator/examples/devopsdojo-dev.yaml
```

### Check Status

```bash
# View CR status
kubectl get devopsdojo -A

# Detailed status
kubectl describe devopsdojo devopsdojo-dev -n devopsdojo-dev

# Watch status changes
kubectl get devopsdojo -A -w
```

Example output:
```
NAME             PHASE   DATABASE   MIGRATION   BACKEND   FRONTEND   AGE
devopsdojo-dev   Ready   true       true        true      true       5m
```

### Update Configuration

```bash
# Scale replicas
kubectl patch devopsdojo devopsdojo-dev -n devopsdojo-dev \
  --type=merge -p '{"spec":{"backend":{"replicas":3}}}'

# Update image
kubectl patch devopsdojo devopsdojo-dev -n devopsdojo-dev \
  --type=merge -p '{"spec":{"backend":{"image":"myrepo/backend:v2"}}}'
```

### Delete Instance

```bash
kubectl delete devopsdojo devopsdojo-dev -n devopsdojo-dev
```

This will cascade delete all managed resources (StatefulSet, Deployments, Services, etc.)

## Configuration Reference

### DevOpsDojo Spec

```yaml
apiVersion: apps.devopsdojo.io/v1
kind: DevOpsDojo
metadata:
  name: my-app
  namespace: my-namespace
spec:
  # PostgreSQL StatefulSet configuration
  database:
    storage: "10Gi"           # PVC size
    storageClass: "gp3"       # Storage class (optional)
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"

  # Backend Deployment configuration
  backend:
    replicas: 2
    image: "myrepo/backend:latest"
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"

  # Frontend Deployment configuration
  frontend:
    replicas: 2
    image: "myrepo/frontend:latest"
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "300m"

  # Ingress configuration (optional)
  ingress:
    enabled: true
    className: "alb"
    host: "myapp.example.com"
    annotations:
      alb.ingress.kubernetes.io/scheme: "internet-facing"

  # External secrets reference (optional)
  # If not provided, operator creates default secrets
  secretsRef: "my-external-secrets"
```

### Required Secrets

If using `secretsRef`, the secret must contain:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-external-secrets
type: Opaque
stringData:
  DB_USERNAME: postgres
  DB_PASSWORD: your-password
  SECRET_KEY: your-flask-secret
```

## Troubleshooting

### Check Operator Logs

```bash
kubectl logs -f deployment/devopsdojo-operator -n devopsdojo-operator-system
```

### Check Component Status

```bash
# Database
kubectl get statefulset -l app=devopsdojo-dev-postgres -n devopsdojo-dev

# Migration job
kubectl get jobs -n devopsdojo-dev
kubectl logs job/devopsdojo-dev-migration -n devopsdojo-dev

# Backend
kubectl get deployment -l app=devopsdojo-dev-backend -n devopsdojo-dev

# Frontend
kubectl get deployment -l app=devopsdojo-dev-frontend -n devopsdojo-dev
```

### Common Issues

**Database not starting:**
- Check PVC is created: `kubectl get pvc -n <namespace>`
- Check storage class exists: `kubectl get storageclass`

**Migration failing:**
- Check migration logs: `kubectl logs job/<name>-migration -n <namespace>`
- Verify database credentials in secrets

**Pods not ready:**
- Check pod events: `kubectl describe pod <pod-name> -n <namespace>`
- Check resource limits and node capacity

## Development

### Run Locally

```bash
# Install dependencies
pip install -r operator/requirements.txt

# Run operator locally (uses kubeconfig)
kopf run operator/src/operator.py --verbose
```

### Run Tests

```bash
# Unit tests
pytest operator/tests/

# Integration tests (requires cluster)
pytest operator/tests/integration/
```

## File Structure

```
operator/
├── Dockerfile
├── requirements.txt
├── README.md
├── install.sh
├── src/
│   └── operator.py          # Main operator code
├── manifests/
│   ├── crd.yaml             # CustomResourceDefinition
│   ├── rbac.yaml            # ServiceAccount, Role, RoleBinding
│   └── operator-deployment.yaml
├── examples/
│   ├── devopsdojo-dev.yaml  # Dev environment CR
│   ├── devopsdojo-prod.yaml # Prod environment CR
│   └── secrets.yaml         # Example secrets
└── templates/
    └── .gitkeep
```

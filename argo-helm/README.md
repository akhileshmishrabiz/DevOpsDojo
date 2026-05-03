# ArgoCD Helm Deployment

Deploy DevOpsDojo using ArgoCD with Helm charts stored in ECR.

## Prerequisites

- ArgoCD installed in cluster
- Helm chart pushed to ECR (see `../helm/README.md`)
- AWS credentials configured for ECR access

## Setup

### 1. Configure ECR Authentication

**Option A: CronJob (recommended)**

```bash
# Create AWS credentials secret
kubectl create secret generic ecr-credentials-sync-aws -n argocd \
  --from-literal=AWS_ACCESS_KEY_ID=<your-key> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<your-secret> \
  --from-literal=AWS_DEFAULT_REGION=ap-south-1

# Apply the CronJob
kubectl apply -f ecr-credentials-cronjob.yaml

# Run once immediately
kubectl create job --from=cronjob/ecr-credentials-sync ecr-credentials-sync-init -n argocd
```

**Option B: IRSA (for EKS)**

Attach ECR read policy to ArgoCD service account - no CronJob needed.

### 2. Update Configuration

Edit the application files and replace:
- `<ACCOUNT_ID>` - Your AWS account ID
- `your-dev-db.rds.amazonaws.com` - Your RDS endpoint
- `devopsdojo.example.com` - Your domain (prod)

### 3. Handle Secrets

**Option A: External Secrets Operator**
```bash
# Install External Secrets Operator first
kubectl apply -f app-secrets.yaml
```

**Option B: Manual (not recommended for prod)**
```bash
kubectl create secret generic devopsdojo-secrets \
  -n devopsdojo-dev \
  --from-literal=DB_PASSWORD=yourpassword \
  --from-literal=SECRET_KEY=yoursecretkey \
  --from-literal=DB_USERNAME=postgres
```

### 4. Deploy Applications

```bash
# Deploy dev
kubectl apply -f application-dev.yaml

# Deploy prod
kubectl apply -f application-prod.yaml
```

## Upgrade Chart Version

1. Push new chart version to ECR
2. Update `targetRevision` in application YAML
3. Commit and push - ArgoCD will sync automatically

```yaml
source:
  targetRevision: 0.2.0  # Update version here
```

## Common Commands

```bash
# Check app status
argocd app get devopsdojo-dev
argocd app get devopsdojo-prod

# Manual sync
argocd app sync devopsdojo-dev

# View diff
argocd app diff devopsdojo-dev

# Rollback
argocd app rollback devopsdojo-dev

# Delete app
argocd app delete devopsdojo-dev
```

## File Structure

```
argo-helm/
├── application-dev.yaml       # Dev ArgoCD Application
├── application-prod.yaml      # Prod ArgoCD Application
├── ecr-repository-secret.yaml # ECR repo config for ArgoCD
├── ecr-credentials-cronjob.yaml # Auto-refresh ECR token
├── app-secrets.yaml           # External Secrets example
└── README.md
```

## Troubleshooting

**ArgoCD can't pull from ECR:**
```bash
# Check if secret exists
kubectl get secret ecr-helm-repo -n argocd

# Check CronJob logs
kubectl logs -l job-name=ecr-credentials-sync -n argocd

# Manually refresh credentials
kubectl create job --from=cronjob/ecr-credentials-sync manual-refresh -n argocd
```

**App stuck in degraded state:**
```bash
# Check events
kubectl get events -n devopsdojo-dev --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -l app.kubernetes.io/name=devopsdojo -n devopsdojo-dev
```

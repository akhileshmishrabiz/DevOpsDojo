# DevOpsDojo Helm Chart

## Prerequisites

- AWS CLI configured with appropriate permissions
- Helm 3.8+ (OCI support)
- kubectl configured for your cluster

## Store Chart in ECR

### 1. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name devopsdojo-helm \
  --region ap-south-1
```

### 2. Authenticate Helm with ECR

```bash
aws ecr get-login-password --region ap-south-1 | \
  helm registry login \
  --username AWS \
  --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
```

### 3. Package and Push Chart

```bash
# Package the chart
helm package ./helm/devopsdojo

# Push to ECR (update version as needed)
helm push devopsdojo-0.1.0.tgz oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
```

## Version Control

Update the version in `helm/devopsdojo/Chart.yaml`:

```yaml
version: 0.1.0      # Chart version - bump this for chart changes
appVersion: "1.0.0" # App version - bump this for app changes
```

**Versioning workflow:**
```bash
# 1. Update Chart.yaml version
# 2. Package with new version
helm package ./helm/devopsdojo

# 3. Push new version to ECR
helm push devopsdojo-0.2.0.tgz oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
```

## Install from ECR

### Development
```bash
helm install devopsdojo \
  oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/devopsdojo-helm \
  --version 0.1.0 \
  -f ./helm/devopsdojo/values-dev.yaml \
  --set database.external.host=your-db.rds.amazonaws.com \
  --set secrets.dbPassword=yourpassword \
  --set secrets.secretKey=yoursecretkey
```

### Production
```bash
helm install devopsdojo \
  oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/devopsdojo-helm \
  --version 0.1.0 \
  -f ./helm/devopsdojo/values-prod.yaml \
  --set database.external.host=your-db.rds.amazonaws.com \
  --set secrets.dbPassword=yourpassword \
  --set secrets.secretKey=yoursecretkey
```

## Common Commands

```bash
# List chart versions in ECR
aws ecr describe-images --repository-name devopsdojo-helm --region ap-south-1

# Pull chart locally
helm pull oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/devopsdojo-helm --version 0.1.0

# Upgrade existing release
helm upgrade devopsdojo \
  oci://<ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/devopsdojo-helm \
  --version 0.2.0 \
  -f ./helm/devopsdojo/values-prod.yaml

# Rollback
helm rollback devopsdojo 1

# Uninstall
helm uninstall devopsdojo
```

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Push Helm Chart to ECR
  run: |
    aws ecr get-login-password --region ap-south-1 | \
      helm registry login --username AWS --password-stdin ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com
    helm package ./helm/devopsdojo
    helm push devopsdojo-*.tgz oci://${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-south-1.amazonaws.com
```

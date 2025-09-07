#!/bin/bash

# Production-grade Monitoring Setup for DevOps Dojo
# Installs Prometheus + Loki + Grafana stack using Helm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE="monitoring"
APP_NAMESPACE="3-tier-app-eks"
S3_BUCKET="devops-dojo-loki-storage"  # Update this to your bucket name
AWS_REGION="us-east-1"

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}  DevOps Dojo - Production Monitoring Setup${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if kubectl is installed and connected
if ! kubectl cluster-info &> /dev/null; then
    print_error "kubectl is not connected to a cluster"
    exit 1
fi
print_status "kubectl is connected to cluster"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    print_error "helm is not installed"
    exit 1
fi
print_status "helm is installed"

# Create S3 bucket for Loki storage (if it doesn't exist)
echo ""
echo -e "${BLUE}Setting up S3 bucket for Loki storage...${NC}"
if ! aws s3 ls "s3://$S3_BUCKET" 2>/dev/null; then
    print_warning "S3 bucket $S3_BUCKET does not exist. Creating..."
    aws s3 mb "s3://$S3_BUCKET" --region $AWS_REGION
    
    # Enable versioning for better data protection
    aws s3api put-bucket-versioning \
        --bucket $S3_BUCKET \
        --versioning-configuration Status=Enabled
    
    # Set lifecycle policy to reduce costs
    cat > /tmp/loki-lifecycle.json <<EOF
{
    "Rules": [
        {
            "ID": "LokiLogRetention",
            "Status": "Enabled",
            "Filter": {"Prefix": ""},
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
EOF
    
    aws s3api put-bucket-lifecycle-configuration \
        --bucket $S3_BUCKET \
        --lifecycle-configuration file:///tmp/loki-lifecycle.json
    
    print_status "S3 bucket $S3_BUCKET created with lifecycle policy"
else
    print_status "S3 bucket $S3_BUCKET already exists"
fi

# Update S3 bucket name in Loki values
sed -i.bak "s/bucketnames: .*/bucketnames: $S3_BUCKET/" monitoring/loki-stack-values.yaml

# Add Helm repositories
echo ""
echo -e "${BLUE}Adding Helm repositories...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
print_status "Helm repositories added and updated"

# Create namespaces
echo ""
echo -e "${BLUE}Creating namespaces...${NC}"
kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace $APP_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
print_status "Namespaces created"

# Label namespaces for monitoring
kubectl label namespace $MONITORING_NAMESPACE monitoring=enabled --overwrite
kubectl label namespace $APP_NAMESPACE monitoring=enabled --overwrite

# Create storage class if it doesn't exist
echo ""
echo -e "${BLUE}Checking storage class...${NC}"
if ! kubectl get storageclass gp3 &> /dev/null; then
    print_warning "GP3 storage class not found, creating..."
    cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
    print_status "GP3 storage class created"
else
    print_status "GP3 storage class exists"
fi

# Install kube-prometheus-stack
echo ""
echo -e "${BLUE}Installing kube-prometheus-stack (Prometheus + Grafana + AlertManager)...${NC}"
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace $MONITORING_NAMESPACE \
  --values monitoring/kube-prometheus-stack-values.yaml \
  --version 51.3.0 \
  --wait \
  --timeout 10m

print_status "kube-prometheus-stack installed successfully"

# Install Loki stack
echo ""
echo -e "${BLUE}Installing Loki stack for logging...${NC}"
helm upgrade --install loki grafana/loki-stack \
  --namespace $MONITORING_NAMESPACE \
  --values monitoring/loki-stack-values.yaml \
  --version 2.9.11 \
  --wait \
  --timeout 10m

print_status "Loki stack installed successfully"

# Wait for pods to be ready
echo ""
echo -e "${BLUE}Waiting for monitoring stack to be ready...${NC}"
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=prometheus" -n $MONITORING_NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=grafana" -n $MONITORING_NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=loki" -n $MONITORING_NAMESPACE --timeout=300s

# Apply ServiceMonitors and additional configurations
echo ""
echo -e "${BLUE}Applying ServiceMonitors and alert rules...${NC}"
kubectl apply -f monitoring/servicemonitors.yaml
kubectl apply -f monitoring/alert-rules.yaml
kubectl apply -f monitoring/grafana-dashboards.yaml

print_status "ServiceMonitors and alert rules applied"

# Create ingress for monitoring services
echo ""
echo -e "${BLUE}Setting up ingress for monitoring services...${NC}"
kubectl apply -f monitoring/monitoring-ingress.yaml
print_status "Monitoring ingress configured"

# Display access information
echo ""
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}  Monitoring Stack Installation Complete!${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""

# Get ingress information
INGRESS_HOST=$(kubectl get ingress monitoring-ingress -n $MONITORING_NAMESPACE -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")

echo -e "${BLUE}Access Information:${NC}"
echo ""
echo "📊 Grafana:"
echo "   URL: http://$INGRESS_HOST/grafana (or kubectl port-forward)"
echo "   Username: admin"
echo "   Password: DevOpsD0j0!2024"
echo ""
echo "🔍 Prometheus:"
echo "   URL: http://$INGRESS_HOST/prometheus (or kubectl port-forward)"
echo ""
echo "📝 Loki:"
echo "   URL: http://$INGRESS_HOST/loki (or kubectl port-forward)"
echo ""
echo "🚨 AlertManager:"
echo "   URL: http://$INGRESS_HOST/alertmanager (or kubectl port-forward)"
echo ""

echo -e "${BLUE}Port Forward Commands (if ingress not working):${NC}"
echo "kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-grafana 3000:80"
echo "kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-kube-prometheus-prometheus 9090:9090"
echo "kubectl port-forward -n $MONITORING_NAMESPACE svc/loki-gateway 3100:80"
echo "kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-kube-prometheus-alertmanager 9093:9093"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo "# Check monitoring pods"
echo "kubectl get pods -n $MONITORING_NAMESPACE"
echo ""
echo "# View Grafana dashboard logs"
echo "kubectl logs -n $MONITORING_NAMESPACE -l app.kubernetes.io/name=grafana"
echo ""
echo "# View Loki logs"
echo "kubectl logs -n $MONITORING_NAMESPACE -l app.kubernetes.io/name=loki"
echo ""
echo "# Check ServiceMonitors"
echo "kubectl get servicemonitors -n $APP_NAMESPACE"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy your applications with metrics endpoints enabled"
echo "2. Configure alerts in AlertManager"
echo "3. Import custom Grafana dashboards"
echo "4. Set up notification channels (Slack, PagerDuty, etc.)"
echo ""

print_status "Monitoring setup completed successfully!"
echo ""
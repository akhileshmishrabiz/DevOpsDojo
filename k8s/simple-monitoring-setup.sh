#!/bin/bash

# Simple Monitoring Setup - Prometheus + Grafana
# Basic installation for learning purposes

set -e

echo "=================================================="
echo "  Simple Monitoring Setup (Prometheus + Grafana)"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Step 1: Add Helm repos
print_step "Adding Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
print_status "Helm repositories added"

# Step 2: Create monitoring namespace
print_step "Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
print_status "Monitoring namespace created"

# Step 3: Install Prometheus
print_step "Installing Prometheus..."
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --set alertmanager.persistentVolume.storageClass="gp2" \
  --set server.persistentVolume.storageClass="gp2" \
  --set server.retention="7d" \
  --wait

print_status "Prometheus installed successfully"

# Step 4: Install Grafana
print_step "Installing Grafana..."
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set persistence.storageClassName="gp2" \
  --set persistence.enabled=true \
  --set adminPassword='Admin123!' \
  --values - <<EOF
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-server.monitoring.svc.cluster.local
      access: proxy
      isDefault: true
EOF

print_status "Grafana installed successfully"

# Step 5: Wait for pods
print_step "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=prometheus" -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=grafana" -n monitoring --timeout=300s

echo ""
echo "=================================================="
echo -e "${GREEN}  Installation Complete!${NC}"
echo "=================================================="
echo ""

echo "Access your services:"
echo ""
echo "📊 Grafana:"
echo "   Port forward: kubectl port-forward -n monitoring svc/grafana 3000:80"
echo "   Then open: http://localhost:3000"
echo "   Username: admin"
echo "   Password: Admin123!"
echo ""
echo "🔍 Prometheus:"
echo "   Port forward: kubectl port-forward -n monitoring svc/prometheus-server 9090:80"
echo "   Then open: http://localhost:9090"
echo ""

echo "Useful commands:"
echo "kubectl get pods -n monitoring"
echo "kubectl logs -n monitoring -l app.kubernetes.io/name=grafana"
echo ""

print_status "Setup completed! Start with port forwarding to access the services."
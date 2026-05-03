#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing DevOpsDojo Operator..."

# Install CRD
echo "Installing CRD..."
kubectl apply -f "$SCRIPT_DIR/manifests/crd.yaml"

# Install RBAC
echo "Installing RBAC..."
kubectl apply -f "$SCRIPT_DIR/manifests/rbac.yaml"

# Install Operator Deployment
echo "Installing Operator..."
kubectl apply -f "$SCRIPT_DIR/manifests/operator-deployment.yaml"

echo ""
echo "Waiting for operator to be ready..."
kubectl rollout status deployment/devopsdojo-operator -n devopsdojo-operator-system --timeout=60s

echo ""
echo "DevOpsDojo Operator installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Create secrets:    kubectl apply -f $SCRIPT_DIR/examples/secrets.yaml"
echo "  2. Deploy app:        kubectl apply -f $SCRIPT_DIR/examples/devopsdojo-dev.yaml"
echo "  3. Check status:      kubectl get devopsdojo -A"

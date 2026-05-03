#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Uninstalling DevOpsDojo Operator..."

# Delete all DevOpsDojo CRs first
echo "Deleting all DevOpsDojo instances..."
kubectl delete devopsdojo --all -A --ignore-not-found

# Wait for resources to be cleaned up
sleep 5

# Delete Operator Deployment
echo "Deleting Operator..."
kubectl delete -f "$SCRIPT_DIR/manifests/operator-deployment.yaml" --ignore-not-found

# Delete RBAC
echo "Deleting RBAC..."
kubectl delete -f "$SCRIPT_DIR/manifests/rbac.yaml" --ignore-not-found

# Delete CRD
echo "Deleting CRD..."
kubectl delete -f "$SCRIPT_DIR/manifests/crd.yaml" --ignore-not-found

echo ""
echo "DevOpsDojo Operator uninstalled successfully!"

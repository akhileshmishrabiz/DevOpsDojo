#!/bin/bash

echo "Testing Kubernetes Deployment Setup"
echo "===================================="

NAMESPACE="3-tier-app-eks"

echo ""
echo "1. Checking if namespace exists..."
kubectl get namespace $NAMESPACE

echo ""
echo "2. Checking backend deployment and service..."
kubectl get deployment backend -n $NAMESPACE
kubectl get service backend -n $NAMESPACE

echo ""
echo "3. Checking frontend deployment and service..."
kubectl get deployment frontend -n $NAMESPACE
kubectl get service frontend -n $NAMESPACE

echo ""
echo "4. Checking pod status..."
kubectl get pods -n $NAMESPACE

echo ""
echo "5. Testing backend service connectivity from frontend pod..."
FRONTEND_POD=$(kubectl get pods -n $NAMESPACE -l app=frontend -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$FRONTEND_POD" ]; then
    echo "Using frontend pod: $FRONTEND_POD"
    echo "Testing backend service DNS resolution..."
    kubectl exec -n $NAMESPACE $FRONTEND_POD -- nslookup backend.$NAMESPACE.svc.cluster.local
    echo ""
    echo "Testing backend health endpoint..."
    kubectl exec -n $NAMESPACE $FRONTEND_POD -- wget -qO- http://backend.$NAMESPACE.svc.cluster.local:8000/health || echo "Failed to reach backend health endpoint"
fi

echo ""
echo "6. Checking frontend logs for errors..."
kubectl logs -n $NAMESPACE -l app=frontend --tail=20

echo ""
echo "7. Checking backend logs for errors..."
kubectl logs -n $NAMESPACE -l app=backend --tail=20

echo ""
echo "8. Checking ingress configuration..."
kubectl get ingress -n $NAMESPACE -o wide

echo ""
echo "===================================="
echo "Test completed. Review the output above for any issues."
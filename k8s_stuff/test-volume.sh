#!/bin/bash

echo "🚀 Starting Kubernetes Volume Test..."
echo "======================================"

# Check if kubectl is configured
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ kubectl not configured or cluster not accessible"
    exit 1
fi

echo "✅ Kubernetes cluster accessible"

# Check current storage classes
echo ""
echo "📊 Current Storage Classes:"
kubectl get storageclass

# Deploy resources
echo ""
echo "🔧 Deploying resources..."
kubectl apply -f storageclass.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

echo ""
echo "⏳ Waiting for resources to be created..."
sleep 10

# Check PVC status
echo ""
echo "💾 PVC Status:"
kubectl get pvc test-ebs-pvc -o wide

# Wait for pod to be ready
echo ""
echo "⏳ Waiting for pod to be ready..."
kubectl wait --for=condition=ready pod -l app=volume-test --timeout=300s

# Check pod status
echo ""
echo "🏃 Pod Status:"
kubectl get pods -l app=volume-test -o wide

# Check if volume is mounted
echo ""
echo "📁 Volume Mount Test:"
if kubectl exec deployment/volume-test-deployment -- test -f /data/test-file.txt; then
    echo "✅ Volume mounted successfully!"
    echo ""
    echo "📄 Volume content:"
    kubectl exec deployment/volume-test-deployment -- cat /data/test-file.txt
    echo ""
    echo "📂 Volume directory listing:"
    kubectl exec deployment/volume-test-deployment -- ls -la /data/
else
    echo "❌ Volume mount failed or file not created"
fi

# Check AWS EBS volume
echo ""
echo "☁️ AWS EBS Volumes:"
PV_NAME=$(kubectl get pvc test-ebs-pvc -o jsonpath='{.spec.volumeName}')
if [ ! -z "$PV_NAME" ]; then
    VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}')
    echo "PV Name: $PV_NAME"
    echo "EBS Volume ID: $VOLUME_ID"
    
    if command -v aws >/dev/null 2>&1; then
        echo "EBS Volume Details:"
        aws ec2 describe-volumes --volume-ids $VOLUME_ID --query 'Volumes[0].[VolumeId,Size,VolumeType,State,Encrypted]' --output table 2>/dev/null || echo "Could not fetch volume details"
    fi
else
    echo "❌ No persistent volume found"
fi

# Test web service
echo ""
echo "🌐 Testing web service:"
kubectl port-forward service/volume-test-service 8080:80 &
PF_PID=$!
sleep 3

if curl -s http://localhost:8080 >/dev/null; then
    echo "✅ Web service accessible"
    echo "🔗 Access at: http://localhost:8080"
    echo "   (Port-forward running in background, PID: $PF_PID)"
else
    echo "❌ Web service not accessible"
    kill $PF_PID 2>/dev/null
fi

echo ""
echo "🎉 Volume test completed!"
echo ""
echo "📋 Summary Commands:"
echo "   kubectl get pvc,pods,svc -l app=volume-test"
echo "   kubectl exec deployment/volume-test-deployment -- df -h /data"
echo "   kubectl logs deployment/volume-test-deployment"
echo ""
echo "🧹 Cleanup:"
echo "   kubectl delete -f ."
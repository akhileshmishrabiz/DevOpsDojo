# Kubernetes Volume Test

This directory contains Kubernetes manifests to test EBS volume provisioning in your EKS cluster.

## Files Overview

- `storageclass.yaml` - Defines GP3 EBS storage class with encryption
- `pvc.yaml` - PersistentVolumeClaim requesting 10Gi storage
- `deployment.yaml` - Nginx deployment with volume mount
- `service.yaml` - ClusterIP service to expose the pod
- `test-volume.sh` - Script to deploy and test everything

## What This Tests

1. **EBS CSI Driver** functionality
2. **Dynamic Volume Provisioning**
3. **Volume mounting** in pods
4. **Data persistence** across pod restarts

## Quick Deploy

```bash
# Deploy all resources
kubectl apply -f .

# Check status
kubectl get pvc,pods,svc -l app=volume-test

# Test volume content
kubectl exec deployment/volume-test-deployment -- ls -la /data/
kubectl exec deployment/volume-test-deployment -- cat /data/test-file.txt
```

## Expected Results

1. **PVC Status**: Should show `Bound` status
2. **EBS Volume**: New 10Gi GP3 volume created in AWS
3. **Pod Status**: Should show `Running` with volume mounted
4. **Data**: Test file should exist in `/data/test-file.txt`

## Troubleshooting

If PVC stays in `Pending`:
```bash
# Check events
kubectl describe pvc test-ebs-pvc

# Check if EBS CSI driver is installed
kubectl get pods -n kube-system | grep ebs-csi

# Check storage classes
kubectl get storageclass
```
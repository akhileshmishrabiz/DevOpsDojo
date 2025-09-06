# Environment Variables Service Discovery

## 🔧 How Kubernetes Automatically Injects Environment Variables

When a pod starts, the **kubelet** (Kubernetes node agent) automatically injects environment variables for **every active service** in the cluster.

## 📋 What Gets Injected

### Core Kubernetes Variables
```bash
# Always present in every pod
KUBERNETES_SERVICE_HOST=10.96.0.1      # Kubernetes API server IP
KUBERNETES_SERVICE_PORT=443             # Kubernetes API server port
KUBERNETES_SERVICE_PORT_HTTPS=443       # HTTPS port variant
```

### Per-Service Variables
For each service named `<SERVICE_NAME>`, Kubernetes creates:
```bash
<SERVICE_NAME>_SERVICE_HOST=<ClusterIP>
<SERVICE_NAME>_SERVICE_PORT=<Port>
<SERVICE_NAME>_SERVICE_PORT_<PORT_NAME>=<Port>  # If port has name
```

## 🎯 Real Example: Our DevOps Dojo Services

### Our Kubernetes Services
```yaml
# k8s/backend.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: 3-tier-app-eks
spec:
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: backend

---
# k8s/frontend.yaml  
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: 3-tier-app-eks
spec:
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: frontend
```

### Auto-Generated Environment Variables

When our frontend pod starts, it automatically gets:

```bash
# Kubernetes core
KUBERNETES_SERVICE_HOST=10.96.0.1
KUBERNETES_SERVICE_PORT=443

# Backend service 
BACKEND_SERVICE_HOST=10.96.87.123
BACKEND_SERVICE_PORT=8000

# Frontend service (yes, even its own service!)
FRONTEND_SERVICE_HOST=10.96.45.67  
FRONTEND_SERVICE_PORT=80

# Plus many more system services...
```

## 🔍 Verify This Yourself

### Check Environment Variables in Running Pod
```bash
# List all Kubernetes-related env vars
kubectl exec -n 3-tier-app-eks deployment/frontend -- env | grep -i service

# Expected output:
KUBERNETES_SERVICE_HOST=10.96.0.1
KUBERNETES_SERVICE_PORT=443
BACKEND_SERVICE_HOST=10.96.87.123
BACKEND_SERVICE_PORT=8000
FRONTEND_SERVICE_HOST=10.96.45.67
FRONTEND_SERVICE_PORT=80
```

### Interactive Shell to Explore
```bash
# Get a shell in the frontend pod
kubectl exec -it -n 3-tier-app-eks deployment/frontend -- /bin/bash

# Inside the pod, check variables
env | grep SERVICE | sort
```

## 🚀 How Our App Uses This

### Detection Logic in `frontend/docker-entrypoint.sh`
```bash
#!/bin/bash

# Line 8: Check if we're in Kubernetes
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    echo "Detected Kubernetes environment"
    # Use Kubernetes service discovery
    NAMESPACE=${NAMESPACE:-3-tier-app-eks}
    BACKEND_URL="http://backend.${NAMESPACE}.svc.cluster.local:8000"
else
    echo "Detected Docker Compose environment"  
    # Use Docker Compose networking
    BACKEND_URL="http://backend:8000"
fi

echo "Using backend URL: $BACKEND_URL"
```

### Why This Works Perfectly

| Environment | `KUBERNETES_SERVICE_HOST` | Detected As | Backend URL |
|-------------|--------------------------|-------------|-------------|
| **Docker Compose** | ❌ Not set | Docker | `http://backend:8000` |
| **Kubernetes** | ✅ `10.96.0.1` | Kubernetes | `http://backend.3-tier-app-eks.svc.cluster.local:8000` |

## ⚡ Environment Variable vs DNS

### Environment Variables Method
```bash
# Use the injected cluster IP directly
curl http://$BACKEND_SERVICE_HOST:$BACKEND_SERVICE_PORT/api/topics
```

**Pros:**
- ✅ Fast (no DNS lookup)
- ✅ Automatic injection
- ✅ Works immediately

**Cons:**
- ❌ Only services that existed when pod started
- ❌ Requires pod restart for new services  
- ❌ Variables for ALL services (cluttered)

### DNS Method (Preferred)
```bash
# Use DNS name that resolves dynamically
curl http://backend.3-tier-app-eks.svc.cluster.local:8000/api/topics
```

**Pros:**
- ✅ Dynamic (no restart needed)
- ✅ Clean, readable
- ✅ Works across namespaces

**Cons:**
- ❌ DNS lookup overhead (minimal)

## 🔬 Deep Dive: When Variables Are Injected

### Timing
```yaml
# Service created at 10:00 AM
kubectl apply -f backend-service.yaml

# Pod started at 10:05 AM  
kubectl apply -f frontend-deployment.yaml
# → Frontend pod gets BACKEND_SERVICE_* variables

# New service created at 10:10 AM
kubectl apply -f new-service.yaml  
# → Frontend pod does NOT get NEW_SERVICE_* variables
# → Need to restart frontend pod to see new service
```

### Solution: Use DNS for New Services
```bash
# This works immediately for new services
curl http://new-service.3-tier-app-eks.svc.cluster.local:8000
```

## 🛠️ Practical Exercises

### Exercise 1: Explore Your Environment
```bash
# Get all service-related environment variables
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep SERVICE

# Count how many services are visible
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep SERVICE_HOST | wc -l
```

### Exercise 2: Create New Service and Test
```bash
# Create a new service
kubectl create service clusterip test-service --tcp=8080:8080 -n 3-tier-app-eks

# Check if frontend pod can see it (should be empty)
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep TEST_SERVICE

# Restart frontend pod
kubectl rollout restart deployment/frontend -n 3-tier-app-eks

# Check again (should now see TEST_SERVICE_HOST)
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep TEST_SERVICE
```

## 📚 Key Takeaways

1. **Automatic**: Kubernetes injects service environment variables without any configuration
2. **Reliable**: `KUBERNETES_SERVICE_HOST` is **guaranteed** to exist in every pod
3. **Static**: Only includes services that existed when the pod started
4. **Detection**: Perfect for environment detection logic
5. **Legacy**: Useful for legacy apps that can't use DNS

## 🔗 Next: DNS-Based Service Discovery

Environment variables are great for detection, but [DNS-based discovery](./03-dns-service-discovery.md) is more flexible for actual service communication!

---

The kubelet is your automatic service discovery assistant! 🤖
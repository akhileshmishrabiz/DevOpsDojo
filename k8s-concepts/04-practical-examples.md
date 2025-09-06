# Practical Examples: Service Discovery in DevOps Dojo

## 🎯 Real-World Implementation

This document shows exactly how our DevOps Dojo application implements service discovery, with actual code and configurations.

## 🏗️ Application Architecture

```mermaid
graph TB
    A[Internet] --> B[ALB Ingress]
    B --> C[Frontend Service]
    C --> D[Frontend Pods]
    D --> E[Backend Service]  
    E --> F[Backend Pods]
    F --> G[PostgreSQL Service]
    G --> H[PostgreSQL Pod]
    
    I[CoreDNS] --> C
    I --> E
    I --> G
```

## 📁 File-by-File Implementation

### 1. Environment Detection (`frontend/docker-entrypoint.sh`)

**The Smart Detection Logic:**
```bash
#!/bin/bash

# Set default backend URL if not provided
if [ -z "$BACKEND_URL" ]; then
    # Try to detect if we're in Kubernetes by checking for service environment variables
    if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
        # In Kubernetes, use the service DNS
        NAMESPACE=${NAMESPACE:-3-tier-app-eks}
        BACKEND_URL="http://backend.${NAMESPACE}.svc.cluster.local:8000"
        echo "🚀 Kubernetes detected - using DNS service discovery"
    else
        # In Docker Compose, use the service name  
        BACKEND_URL="http://backend:8000"
        echo "🐳 Docker Compose detected - using service names"
    fi
fi

echo "Using backend URL: $BACKEND_URL"

# Replace environment variables in the Nginx config
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf

echo "Generated Nginx configuration:"
cat /etc/nginx/conf.d/default.conf

nginx -g "daemon off;"
```

**Why This Works:**
- `KUBERNETES_SERVICE_HOST` is automatically set by kubelet in every pod
- DNS service discovery uses full FQDN for reliability
- Same Docker image works in both environments

### 2. Frontend API Configuration (`frontend/src/config/api.js`)

**Simplified API Configuration:**
```javascript
// Use empty string to make all API calls relative to the current origin
// This allows nginx to proxy /api calls to the backend
const API_URL = '';

export default API_URL;
```

**Key Benefits:**
- No hardcoded URLs in React build
- All API calls go to `/api` (relative paths)
- Nginx handles the proxying to backend service

### 3. Nginx Proxy Template (`frontend/nginx.conf.template`)

**Dynamic Backend Proxying:**
```nginx
server {
    listen 80;
    
    # Serve static React app files
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy /api requests to the backend service
    location /api {
        # This gets replaced at runtime with the backend URL
        proxy_pass ${BACKEND_URL};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Runtime Transformation:**

In **Docker Compose**, becomes:
```nginx
proxy_pass http://backend:8000;
```

In **Kubernetes**, becomes:
```nginx
proxy_pass http://backend.3-tier-app-eks.svc.cluster.local:8000;
```

### 4. Kubernetes Service Definitions (`k8s/backend.yaml`, `k8s/frontend.yaml`)

**Backend Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: 3-tier-app-eks
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Frontend Service:**
```yaml
apiVersion: v1  
kind: Service
metadata:
  name: frontend
  namespace: 3-tier-app-eks
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

**What Kubernetes Creates Automatically:**
```bash
# DNS Records
backend.3-tier-app-eks.svc.cluster.local → 10.96.87.123
frontend.3-tier-app-eks.svc.cluster.local → 10.96.45.67

# Environment Variables (in all pods)
KUBERNETES_SERVICE_HOST=10.96.0.1
BACKEND_SERVICE_HOST=10.96.87.123  
BACKEND_SERVICE_PORT=8000
FRONTEND_SERVICE_HOST=10.96.45.67
FRONTEND_SERVICE_PORT=80
```

### 5. Frontend Deployment Configuration (`k8s/frontend.yaml`)

**Namespace Injection:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: 3-tier-app-eks
spec:
  template:
    spec:
      containers:
      - name: frontend
        image: livingdevopswithakhilesh/devopsdozo:frontend-latest
        env:
        - name: NAMESPACE
          value: "3-tier-app-eks"
```

**Why NAMESPACE is Important:**
- Allows the entrypoint script to build correct DNS names
- Makes the deployment namespace-aware
- Enables easy environment promotion (dev/staging/prod)

## 🚀 Request Flow Examples

### Frontend → Backend API Call

**1. Browser Request:**
```javascript
// From React app
fetch('/api/topics')
```

**2. Nginx Receives Request:**
```bash
GET /api/topics HTTP/1.1
Host: frontend.example.com
```

**3. Nginx Proxies to Backend:**
```bash
# In Kubernetes
GET http://backend.3-tier-app-eks.svc.cluster.local:8000/api/topics

# In Docker Compose  
GET http://backend:8000/api/topics
```

**4. DNS Resolution:**
```bash
# CoreDNS resolves backend.3-tier-app-eks.svc.cluster.local
# Returns: 10.96.87.123
```

**5. Load Balancing:**
```bash
# Service forwards to healthy backend pod
GET http://10.244.1.15:8000/api/topics  # Pod IP
```

### Backend → Database Connection

**Backend Application Code:**
```python
# backend/app/config.py
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:postgres@postgres-db.3-tier-app-eks.svc.cluster.local:5432/devops_learning'
)
```

**Service Resolution:**
```bash
# DNS lookup
postgres-db.3-tier-app-eks.svc.cluster.local → 10.96.200.45

# Direct connection to PostgreSQL pod
postgresql://postgres:postgres@10.244.2.30:5432/devops_learning
```

## 🧪 Testing Service Discovery

### Test 1: Environment Detection
```bash
# Deploy to Docker Compose
docker-compose up -d
docker-compose logs frontend | grep "backend URL"
# Output: Using backend URL: http://backend:8000

# Deploy to Kubernetes  
kubectl apply -f k8s/
kubectl logs -n 3-tier-app-eks deployment/frontend | grep "backend URL"
# Output: Using backend URL: http://backend.3-tier-app-eks.svc.cluster.local:8000
```

### Test 2: DNS Resolution
```bash
# From inside frontend pod in Kubernetes
kubectl exec -n 3-tier-app-eks deployment/frontend -- nslookup backend

# Output:
# Name:    backend.3-tier-app-eks.svc.cluster.local
# Address: 10.96.87.123
```

### Test 3: API Connectivity  
```bash
# Test API through frontend proxy
curl http://localhost:3000/api/topics

# Test backend directly (Docker Compose)
curl http://localhost:8000/api/topics

# Both should return same JSON:
# [{"id":"docker","title":"Docker","description":"..."}]
```

## 🔄 Multi-Environment Support

### Development (Docker Compose)
```yaml
# docker-compose.yml
services:
  frontend:
    environment:
      - BACKEND_URL=http://backend:8000  # Simple service name
  backend:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/devops_learning
```

### Staging (Kubernetes)
```yaml
# k8s/staging/frontend.yaml
env:
- name: NAMESPACE
  value: "devops-staging"
```
**Generated URL:** `http://backend.devops-staging.svc.cluster.local:8000`

### Production (Kubernetes) 
```yaml
# k8s/production/frontend.yaml
env:
- name: NAMESPACE
  value: "devops-production"
```
**Generated URL:** `http://backend.devops-production.svc.cluster.local:8000`

## 🏆 Benefits Achieved

### 1. Single Container Image
- ✅ Same image works in dev, staging, production
- ✅ No environment-specific builds
- ✅ Simplified CI/CD pipeline

### 2. Automatic Service Discovery
- ✅ No hardcoded IPs or URLs
- ✅ Services can move and scale freely
- ✅ Built-in load balancing

### 3. Environment Agnostic
- ✅ Detects environment automatically
- ✅ Adapts networking approach accordingly
- ✅ Zero configuration needed

### 4. Kubernetes-Native
- ✅ Leverages built-in service discovery
- ✅ Uses standard Kubernetes patterns
- ✅ Compatible with service mesh (future)

## 🔧 Troubleshooting Real Issues

### Issue 1: 500 Errors (Missing Tables)
**Problem:** Backend returns 500 errors because database tables don't exist

**Root Cause:** Migration not running before backend starts

**Solution:** Added migration dependency in docker-compose.yml
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy
  command: bash -c "sleep 10 && ./migrate.sh && gunicorn --bind 0.0.0.0:8000 run:app"
```

### Issue 2: Frontend Can't Reach Backend  
**Problem:** API calls to `/api/topics` fail with connection errors

**Root Cause:** Nginx proxy configuration not using correct backend URL

**Solution:** Fixed nginx template to use `${BACKEND_URL}` substitution
```nginx
# Before (broken)
proxy_pass $BACKEND_SERVICE_URL/api;

# After (working)  
proxy_pass ${BACKEND_URL};
```

### Issue 3: Different Behavior in K8s vs Docker
**Problem:** Works in Docker Compose but fails in Kubernetes

**Root Cause:** Hardcoded service discovery approach

**Solution:** Implemented environment detection
```bash
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    # Kubernetes-specific logic
else  
    # Docker Compose logic
fi
```

## 🔗 Related Files in Our Repository

- `/frontend/docker-entrypoint.sh` - Environment detection logic
- `/frontend/nginx.conf.template` - Nginx proxy template  
- `/frontend/src/config/api.js` - Frontend API configuration
- `/k8s/frontend.yaml` - Kubernetes frontend deployment
- `/k8s/backend.yaml` - Kubernetes backend service
- `/docker-compose.yml` - Docker Compose configuration

## 📚 Key Takeaways

1. **Environment Detection**: Use `KUBERNETES_SERVICE_HOST` to detect environment
2. **DNS is King**: Use full FQDN for reliability in Kubernetes
3. **Runtime Configuration**: Generate configs at container startup, not build time
4. **Single Image**: One container image for all environments
5. **Graceful Degradation**: Handle both simple and complex networking

---

This is service discovery in action - elegant, automatic, and production-ready! 🎯
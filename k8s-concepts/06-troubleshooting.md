# Troubleshooting Service Discovery

## 🔍 Common Service Discovery Issues

This guide covers real-world service discovery problems and their solutions, with examples from our DevOps Dojo application.

## 🚨 Issue Categories

### 1. DNS Resolution Problems
### 2. Environment Variable Issues  
### 3. Network Connectivity Problems
### 4. Configuration Errors
### 5. Timing and Dependency Issues

---

## 1️⃣ DNS Resolution Problems

### Issue: Service Not Found
```bash
# Error message
nslookup: can't resolve 'backend.3-tier-app-eks.svc.cluster.local'
curl: (6) Could not resolve host: backend
```

#### Diagnostic Steps
```bash
# 1. Check if service exists
kubectl get svc -n 3-tier-app-eks backend
kubectl describe svc -n 3-tier-app-eks backend

# 2. Check CoreDNS status
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# 3. Test DNS from pod
kubectl exec -n 3-tier-app-eks deployment/frontend -- nslookup backend
kubectl exec -n 3-tier-app-eks deployment/frontend -- cat /etc/resolv.conf
```

#### Common Causes & Solutions

**Cause 1: Wrong Namespace**
```bash
# Wrong - assumes default namespace
curl http://backend:8000

# Right - specify namespace  
curl http://backend.3-tier-app-eks:8000
curl http://backend.3-tier-app-eks.svc.cluster.local:8000
```

**Cause 2: Service Doesn't Exist**
```bash
# Check all services
kubectl get svc -A | grep backend

# Create missing service
kubectl apply -f k8s/backend.yaml
```

**Cause 3: Typo in Service Name**
```bash
# Check exact service name
kubectl get svc -n 3-tier-app-eks

# Common typos
beckend.3-tier-app-eks.svc.cluster.local  # Wrong: beckend
backend.3-teir-app-eks.svc.cluster.local  # Wrong: teir
backend.3-tier-app-eks.srv.cluster.local  # Wrong: srv
```

### Issue: Intermittent DNS Failures
```bash
# Sometimes works, sometimes doesn't
curl: (6) Could not resolve host: backend (50% failure rate)
```

#### Diagnostic Steps
```bash
# 1. Check CoreDNS load and errors
kubectl top pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100

# 2. Test DNS server directly
kubectl exec -n 3-tier-app-eks deployment/frontend -- nslookup backend 10.96.0.10

# 3. Check DNS cache settings
kubectl exec -n 3-tier-app-eks deployment/frontend -- cat /etc/resolv.conf
```

#### Solutions
```bash
# 1. Scale CoreDNS if overloaded
kubectl scale deployment coredns -n kube-system --replicas=3

# 2. Configure local DNS caching
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: nodelocaldns-config
  namespace: kube-system
data:
  Corefile: |
    cluster.local:53 {
        cache {
                success 9984 30
                denial 9984 5
        }
        # ... other configs
    }
EOF
```

---

## 2️⃣ Environment Variable Issues

### Issue: KUBERNETES_SERVICE_HOST Not Set
```bash
# In our app's docker-entrypoint.sh
echo "Environment variables:"
env | grep KUBERNETES
# No output - variable missing
```

#### Diagnostic Steps
```bash
# 1. Check if running in Kubernetes
kubectl get pods -n 3-tier-app-eks

# 2. Check environment variables in pod
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep KUBERNETES

# 3. Check pod specification
kubectl describe pod -n 3-tier-app-eks -l app=frontend
```

#### Common Causes & Solutions

**Cause 1: Running in Docker Compose**
```bash
# Expected behavior - Docker Compose doesn't set this variable
# Solution: Detection logic should handle this
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    echo "Running in Kubernetes"
else
    echo "Running in Docker Compose"  # This is normal
fi
```

**Cause 2: Pod Not Created by Kubernetes**
```bash
# Wrong: Direct docker run
docker run my-app

# Right: Kubernetes deployment
kubectl apply -f k8s/frontend.yaml
```

### Issue: Service Environment Variables Missing
```bash
# Expected variables not found
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep BACKEND_SERVICE
# No output
```

#### Diagnostic Steps
```bash
# 1. Check if service exists and was created before pod
kubectl get svc -n 3-tier-app-eks backend
kubectl describe svc -n 3-tier-app-eks backend

# 2. Check pod creation time vs service creation time
kubectl get svc -n 3-tier-app-eks backend -o yaml | grep creationTimestamp
kubectl get pod -n 3-tier-app-eks -l app=frontend -o yaml | grep creationTimestamp

# 3. Restart pods to get updated environment variables
kubectl rollout restart deployment/frontend -n 3-tier-app-eks
```

#### Root Cause & Solution
```bash
# Problem: Service created after pod started
# Kubernetes only injects environment variables for services that exist when pod starts

# Solution 1: Restart deployment
kubectl rollout restart deployment/frontend -n 3-tier-app-eks

# Solution 2: Use DNS instead (recommended)
# DNS discovery works for services created after pods
curl http://backend.3-tier-app-eks.svc.cluster.local:8000
```

---

## 3️⃣ Network Connectivity Problems

### Issue: DNS Resolves But Connection Fails
```bash
# DNS works
nslookup backend.3-tier-app-eks.svc.cluster.local
# backend.3-tier-app-eks.svc.cluster.local has address 10.96.87.123

# But connection fails
curl http://backend.3-tier-app-eks.svc.cluster.local:8000
# curl: (7) Failed to connect to backend.3-tier-app-eks.svc.cluster.local port 8000: Connection refused
```

#### Diagnostic Steps
```bash
# 1. Check service endpoints
kubectl get endpoints -n 3-tier-app-eks backend
kubectl describe endpoints -n 3-tier-app-eks backend

# 2. Check pod status
kubectl get pods -n 3-tier-app-eks -l app=backend
kubectl describe pods -n 3-tier-app-eks -l app=backend

# 3. Test pod directly
kubectl exec -n 3-tier-app-eks deployment/frontend -- curl http://10.244.1.15:8000/api/topics

# 4. Check port configuration
kubectl get svc -n 3-tier-app-eks backend -o yaml
```

#### Common Causes & Solutions

**Cause 1: No Healthy Pods**
```bash
# Check pod status
kubectl get pods -n 3-tier-app-eks -l app=backend
# NAME                       READY   STATUS    RESTARTS   AGE
# backend-xxx                0/1     Pending   0          5m

# Check why pod not ready
kubectl describe pod -n 3-tier-app-eks backend-xxx

# Common issues:
# - Image pull errors
# - Resource constraints  
# - Failed health checks
```

**Cause 2: Wrong Port Configuration**
```yaml
# Wrong service port
apiVersion: v1
kind: Service
spec:
  ports:
  - port: 8000
    targetPort: 80  # Wrong! Backend listens on 8000

# Right configuration  
apiVersion: v1
kind: Service
spec:
  ports:
  - port: 8000
    targetPort: 8000  # Correct!
```

**Cause 3: Selector Mismatch**
```yaml
# Service selector
apiVersion: v1
kind: Service
spec:
  selector:
    app: backend-service  # Wrong!

# Deployment labels  
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    metadata:
      labels:
        app: backend  # Mismatch!

# Fix: Make them match
spec:
  selector:
    app: backend
```

---

## 4️⃣ Configuration Errors

### Issue: Wrong Nginx Backend URL
```bash
# Frontend logs show wrong URL
docker-compose logs frontend | grep "backend URL"
# Using backend URL: http://backend.undefined.svc.cluster.local:8000
```

#### Diagnostic Steps
```bash
# 1. Check environment variables in container
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep NAMESPACE

# 2. Check frontend deployment configuration
kubectl get deployment -n 3-tier-app-eks frontend -o yaml | grep -A 10 env

# 3. Check generated nginx configuration
kubectl exec -n 3-tier-app-eks deployment/frontend -- cat /etc/nginx/conf.d/default.conf
```

#### Root Cause & Solution
```yaml
# Problem: NAMESPACE variable not set in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  template:
    spec:
      containers:
      - name: frontend
        env:
        # Missing NAMESPACE variable!

# Solution: Add NAMESPACE environment variable
apiVersion: apps/v1  
kind: Deployment
metadata:
  name: frontend
spec:
  template:
    spec:
      containers:
      - name: frontend
        env:
        - name: NAMESPACE
          value: "3-tier-app-eks"
```

### Issue: API Calls Return 404
```bash
# Frontend can reach backend but gets 404
curl http://localhost:3000/api/topics
# 404 Not Found
```

#### Diagnostic Steps
```bash
# 1. Check nginx proxy configuration
kubectl exec -n 3-tier-app-eks deployment/frontend -- cat /etc/nginx/conf.d/default.conf

# 2. Test backend directly
kubectl exec -n 3-tier-app-eks deployment/frontend -- curl http://backend:8000/api/topics

# 3. Check nginx access logs
kubectl logs -n 3-tier-app-eks deployment/frontend
```

#### Common Causes & Solutions

**Cause 1: Double /api in URL**
```nginx
# Wrong nginx config
location /api {
    proxy_pass http://backend:8000/api;  # Creates /api/api/topics
}

# Right nginx config
location /api {
    proxy_pass http://backend:8000;  # Creates /api/topics
}
```

**Cause 2: Backend Not Listening on Expected Path**
```python
# Check backend route registration
# backend/app/routes/__init__.py
topic_bp = Blueprint('topics', __name__, url_prefix='/api/topics')  # Wrong!
topic_bp = Blueprint('topics', __name__, url_prefix='/topics')     # Right!

# backend/app/__init__.py
app.register_blueprint(topic_bp, url_prefix='/api')  # This creates /api/topics
```

---

## 5️⃣ Timing and Dependency Issues

### Issue: Backend Starts Before Database Ready
```bash
# Backend logs show database connection errors
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) 
could not connect to server: Connection refused
```

#### Diagnostic Steps
```bash
# 1. Check database pod status
kubectl get pods -n 3-tier-app-eks -l app=postgres
kubectl logs -n 3-tier-app-eks -l app=postgres

# 2. Check backend startup timing
kubectl logs -n 3-tier-app-eks -l app=backend --timestamps

# 3. Test database connectivity
kubectl exec -n 3-tier-app-eks deployment/backend -- nc -zv postgres-db 5432
```

#### Solutions

**Solution 1: Init Containers**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      initContainers:
      - name: wait-for-db
        image: busybox
        command: ['sh', '-c', 'until nslookup postgres-db; do echo waiting for database; sleep 2; done;']
      containers:
      - name: backend
        # ... backend container spec
```

**Solution 2: Application-Level Retry**
```python
# backend/app/__init__.py
import time
import sys
from sqlalchemy.exc import OperationalError

def wait_for_db(app, max_retries=30):
    """Wait for database to be ready"""
    for attempt in range(max_retries):
        try:
            with app.app_context():
                db.engine.execute('SELECT 1')
            print("Database connection successful!")
            return
        except OperationalError as e:
            print(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2)
    
    print("Failed to connect to database after all retries")
    sys.exit(1)

def create_app():
    app = Flask(__name__)
    # ... app configuration
    wait_for_db(app)
    return app
```

**Solution 3: Kubernetes Probes**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health  
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 🛠️ Debugging Tools and Commands

### DNS Debugging Toolkit
```bash
# Basic DNS testing
kubectl exec -n 3-tier-app-eks deployment/frontend -- nslookup backend
kubectl exec -n 3-tier-app-eks deployment/frontend -- dig backend.3-tier-app-eks.svc.cluster.local

# DNS server testing
kubectl exec -n 3-tier-app-eks deployment/frontend -- nslookup backend 10.96.0.10

# DNS configuration
kubectl exec -n 3-tier-app-eks deployment/frontend -- cat /etc/resolv.conf
```

### Network Connectivity Testing
```bash
# Port connectivity
kubectl exec -n 3-tier-app-eks deployment/frontend -- nc -zv backend 8000
kubectl exec -n 3-tier-app-eks deployment/frontend -- telnet backend 8000

# HTTP testing
kubectl exec -n 3-tier-app-eks deployment/frontend -- curl -v http://backend:8000/api/topics
kubectl exec -n 3-tier-app-eks deployment/frontend -- wget -qO- http://backend:8000/health
```

### Service Investigation
```bash
# Service details
kubectl get svc -n 3-tier-app-eks -o wide
kubectl describe svc -n 3-tier-app-eks backend
kubectl get endpoints -n 3-tier-app-eks backend

# Pod investigation  
kubectl get pods -n 3-tier-app-eks -o wide -l app=backend
kubectl describe pods -n 3-tier-app-eks -l app=backend
kubectl logs -n 3-tier-app-eks -l app=backend --tail=50
```

### Environment Variable Debugging
```bash
# Check all service-related variables
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep SERVICE | sort

# Check Kubernetes detection variables
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep KUBERNETES

# Check custom variables
kubectl exec -n 3-tier-app-eks deployment/frontend -- printenv | grep NAMESPACE
```

## 📋 Troubleshooting Checklist

### Before Debugging
- [ ] Confirm the issue is service discovery related
- [ ] Check if it's environment-specific (Docker vs Kubernetes)
- [ ] Gather relevant logs and error messages

### DNS Issues
- [ ] Verify service exists: `kubectl get svc`
- [ ] Check service has endpoints: `kubectl get endpoints`
- [ ] Test DNS resolution: `nslookup` from pod
- [ ] Verify CoreDNS is running: `kubectl get pods -n kube-system`
- [ ] Check for typos in service names

### Network Issues  
- [ ] Test direct pod connectivity
- [ ] Verify port configuration in service
- [ ] Check selector matches deployment labels
- [ ] Confirm pods are ready and healthy

### Configuration Issues
- [ ] Check nginx/proxy configuration
- [ ] Verify environment variables are set
- [ ] Test backend endpoints directly
- [ ] Review application route configuration

### Timing Issues
- [ ] Check startup order and dependencies
- [ ] Add appropriate init containers or wait logic
- [ ] Implement proper health checks
- [ ] Review resource constraints

## 🚀 Prevention Best Practices

1. **Use Health Checks**: Implement proper readiness and liveness probes
2. **Environment Detection**: Build apps that adapt to their environment  
3. **DNS Over Environment Variables**: Prefer DNS for service discovery
4. **Proper Error Handling**: Handle service discovery failures gracefully
5. **Monitoring**: Monitor service discovery metrics and failures
6. **Testing**: Test service discovery in all target environments

---

Most service discovery issues are configuration problems in disguise! 🔍
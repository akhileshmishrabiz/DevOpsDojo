# 🚀 How to Run the Complete Metrics Demo

## 📋 Prerequisites

- Kubernetes cluster (local or cloud)
- kubectl configured
- Helm installed
- Docker (for building custom images, optional)

## 🎯 Complete Demo Setup (15 minutes)

### Step 1: Deploy Monitoring Infrastructure
```bash
cd k8s

# Install Prometheus + Grafana
./simple-monitoring-setup.sh

# Wait for pods to be ready
kubectl get pods -n monitoring -w
```

### Step 2: Deploy Database Metrics
```bash
# Add PostgreSQL exporter for database metrics
kubectl apply -f simple-postgres-exporter.yaml

# Verify it's running
kubectl get pods -n 3-tier-app-eks | grep postgres-exporter
```

### Step 3: Configure Service Discovery
```bash
# Tell Prometheus where to find your app metrics
kubectl apply -f simple-servicemonitor.yaml

# Check ServiceMonitors
kubectl get servicemonitors -n 3-tier-app-eks
```

### Step 4: Access Grafana Dashboard
```bash
# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80 &

# Login to Grafana
echo "Grafana: http://localhost:3000"
echo "Username: admin"
echo "Password: Admin123!"
```

### Step 5: Import Comprehensive Dashboard
1. Open Grafana: http://localhost:3000
2. Click **"+"** → **"Import"**
3. Copy the entire contents of `k8s/comprehensive-dashboard.json`
4. Paste into the import box
5. Click **"Import"**

### Step 6: Run Backend with Metrics (Local Testing)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run Flask app with metrics
python app.py

# Test metrics endpoint
curl http://localhost:8000/metrics

# Test API endpoints
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

curl http://localhost:8000/api/products
```

### Step 7: Run Frontend with Metrics (Optional)
```bash
cd frontend

# Install dependencies
npm install

# Start React app
npm start

# Open in browser: http://localhost:3001
# Click buttons to generate metrics
```

### Step 8: Generate Test Traffic
```bash
cd k8s

# Deploy load test to generate metrics
kubectl apply -f load-test.yaml

# Watch the job progress
kubectl get jobs -w

# Check load test logs
kubectl logs -f job/load-test
```

## 📊 What You Should See

### In Grafana Dashboard (after 2-3 minutes):

#### 🚀 Request Rate Panel
- Shows requests per second from your load test
- Should increase from 0 to 10-20 RPS during load test

#### ❌ Error Rate Panel  
- Shows percentage of failed requests
- Should stay low (green) during normal operation

#### ⏱️ Response Time Panel
- Shows P95 response time in milliseconds
- Should be < 500ms for healthy application

#### 🖥️ Active Pods Panel
- Shows number of running application pods
- Should show 2-4 pods depending on your setup

#### 📈 Memory & CPU Panels
- Shows resource usage by pod
- Will increase during load test

#### 🗄️ Database Panels
- Shows PostgreSQL metrics
- Connections, query performance, database size

### In Prometheus (http://localhost:9090):

Try these queries:
```promql
# Basic metrics check
up

# HTTP requests
rate(http_requests_total[5m])

# Database connections
pg_stat_database_numbackends

# Pod memory usage
sum(container_memory_working_set_bytes{namespace="3-tier-app-eks"}) by (pod)
```

## 🎭 Demo Scenarios

### Scenario 1: Normal Operations
```bash
# Generate steady traffic
kubectl apply -f load-test.yaml

# Watch metrics in Grafana
# Expected: Steady request rate, low error rate, normal response times
```

### Scenario 2: Simulate High Load
```bash
# Edit load-test.yaml to increase parallelism
sed -i 's/parallelism: 3/parallelism: 10/' load-test.yaml
kubectl apply -f load-test.yaml

# Watch metrics spike in Grafana
# Expected: Higher request rate, possibly higher response times
```

### Scenario 3: Backend Error Simulation
```bash
# If running backend locally, call error endpoint
curl http://localhost:8000/simulate/errors

# Or create a broken endpoint and call it repeatedly
for i in {1..50}; do
  curl -s http://localhost:8000/api/nonexistent || true
  sleep 1
done

# Watch error rate increase in Grafana
```

### Scenario 4: Database Load
```bash
# Call endpoints that query the database repeatedly
for i in {1..100}; do
  curl -s http://localhost:8000/api/products?limit=50 || true
  sleep 0.5
done

# Watch database metrics in Grafana
# Expected: Increased query rate, possibly higher query times
```

## 🔍 Exploring the Data

### Key Metrics to Watch

#### Application Health
- **Request Rate**: Steady traffic indicates healthy app
- **Error Rate**: Should be < 1% in normal conditions
- **Response Time**: P95 should be < 500ms

#### Resource Usage  
- **Memory**: Should be stable, not constantly increasing
- **CPU**: Should correlate with request rate
- **Database Connections**: Should be reasonable (< 20 for small app)

#### Business Metrics (if you have business endpoints)
- **User Registrations**: Track signups
- **Orders Created**: Track purchases
- **Revenue**: Track business value

### Advanced Exploration

#### Custom Queries in Prometheus
```promql
# Error rate by endpoint
sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (endpoint) 
/ sum(rate(http_requests_total[5m])) by (endpoint) * 100

# Top slowest endpoints
topk(5, histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
))

# Memory usage trend
increase(container_memory_working_set_bytes[1h])
```

#### Dashboard Customization
1. Click **Edit** on any panel
2. Modify the query or visualization
3. Save changes
4. Create your own panels

## 🛠️ Troubleshooting

### Metrics Not Appearing?
```bash
# Check if Prometheus can reach your services
kubectl get servicemonitors -A

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
# Visit: http://localhost:9090/targets

# Check pod logs
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus
```

### Load Test Not Working?
```bash
# Check load test job status
kubectl describe job load-test -n 3-tier-app-eks

# Check load test logs  
kubectl logs job/load-test -n 3-tier-app-eks

# Manually test endpoints
kubectl port-forward -n 3-tier-app-eks svc/backend 8000:8000
curl http://localhost:8000/health
```

### Grafana Dashboard Empty?
1. Check data source configuration
2. Verify time range (last 1 hour)
3. Ensure metrics are being generated
4. Check for typos in metric names

## 🎓 Learning Objectives

After completing this demo, you should understand:

### Technical Skills
- How Prometheus collects metrics via service discovery
- How to create Grafana dashboards and queries  
- How to instrument applications with metrics
- How to monitor Kubernetes workloads

### Business Skills  
- The importance of observability in production systems
- How to define and track SLIs/SLOs
- Cost implications of different monitoring approaches
- How metrics drive business decisions

### DevOps Skills
- Infrastructure as Code for monitoring
- Helm chart management and customization
- Kubernetes service discovery patterns
- Production readiness considerations

## 🚀 Next Steps

1. **Customize the dashboard** with metrics specific to your use case
2. **Add alerting rules** for important thresholds
3. **Implement business-specific metrics** in your applications
4. **Set up log aggregation** with Loki (see PLG stack guide)
5. **Add distributed tracing** with Jaeger
6. **Implement cost optimization** strategies

## 📞 Need Help?

- Check the `monitoring-docs/` folder for detailed guides
- Review example code for common patterns
- Test individual components step by step
- Use `kubectl describe` and `kubectl logs` for debugging

**Remember: Start simple, then build complexity as you learn! This demo provides a solid foundation for production monitoring.** 🎯
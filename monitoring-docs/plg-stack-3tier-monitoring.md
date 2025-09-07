# Production Monitoring with Prometheus, Loki, and Grafana (PLG Stack) for 3-Tier Application

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Cost Analysis](#cost-analysis)
4. [Implementation Guide](#implementation-guide)
5. [Application Instrumentation](#application-instrumentation)
6. [Production Concepts](#production-concepts)
7. [Dashboards and Alerts](#dashboards-and-alerts)
8. [Troubleshooting](#troubleshooting)
9. [Demo Scenarios](#demo-scenarios)

## Overview

The PLG (Prometheus, Loki, Grafana) stack is the cloud-native, open-source monitoring solution that's become the de facto standard for Kubernetes. This guide implements production-grade monitoring for your 3-tier application on EKS.

### Why PLG Stack?

| Aspect | PLG Stack | CloudWatch | ELK Stack |
|--------|-----------|------------|-----------|
| **Cost** | 💚 Low (~$50-100/month) | 🔴 High (~$500+/month) | 🟡 Medium (~$200/month) |
| **Complexity** | 🟡 Medium | 💚 Low | 🔴 High |
| **Kubernetes Native** | 💚 Yes | 🔴 No | 🟡 Partial |
| **Vendor Lock-in** | 💚 None | 🔴 AWS Only | 💚 None |
| **Query Language** | PromQL/LogQL | CloudWatch Insights | Elasticsearch DSL |
| **Cardinality Handling** | 🟡 Careful planning needed | 💚 Managed | 🔴 Can be expensive |

### Stack Components

```
┌────────────────────────────────────────────────────────────┐
│                     Grafana (UI Layer)                      │
│           Dashboards │ Alerts │ Explore │ Reports          │
└──────────────┬─────────────────────┬──────────────────────┘
               │                     │
        Metrics│              Logs   │
               ▼                     ▼
┌──────────────────────┐  ┌──────────────────────┐
│     Prometheus       │  │        Loki          │
│  (Metrics Storage)   │  │   (Log Aggregation)  │
└──────────┬───────────┘  └──────────┬───────────┘
           │                          │
           │ Pull                     │ Push
           ▼                          ▼
┌──────────────────────────────────────────────────┐
│              Your 3-Tier Application              │
├──────────────┬───────────────┬───────────────────┤
│   Frontend   │    Backend    │    Database       │
│   (React)    │  (Flask/Python)│  (PostgreSQL)    │
│              │               │                    │
│ /metrics     │  /metrics     │  postgres_exporter│
│ console logs │  app logs     │  query logs       │
└──────────────┴───────────────┴───────────────────┘
```

## Architecture

### Detailed Component Architecture

```yaml
Monitoring Namespace:
├── Prometheus Components:
│   ├── Prometheus Server (2 replicas, HA)
│   ├── AlertManager (Handle alerts)
│   ├── Pushgateway (For batch jobs)
│   └── Node Exporter (DaemonSet on each node)
│
├── Loki Components:
│   ├── Loki Distributor (Receives logs)
│   ├── Loki Ingester (Processes logs)
│   ├── Loki Querier (Queries logs)
│   └── Promtail (DaemonSet, ships logs)
│
└── Grafana Components:
    ├── Grafana Server (UI)
    ├── Grafana Image Renderer (PDF exports)
    └── Grafana Database (SQLite/PostgreSQL)

Application Namespace (3-tier-app-eks):
├── Frontend Service:
│   ├── Deployment (2 replicas)
│   ├── Service (ClusterIP)
│   └── ServiceMonitor (Prometheus discovery)
│
├── Backend Service:
│   ├── Deployment (2 replicas)
│   ├── Service (ClusterIP)
│   ├── ServiceMonitor
│   └── PodMonitor (for custom metrics)
│
└── Database:
    ├── StatefulSet (PostgreSQL)
    ├── Service (Headless)
    ├── PostgreSQL Exporter
    └── ServiceMonitor
```

### Data Flow

1. **Metrics Flow**: Application → Prometheus → Grafana
2. **Logs Flow**: Application → Promtail → Loki → Grafana
3. **Alerts Flow**: Prometheus → AlertManager → Slack/PagerDuty

## Cost Analysis

### Infrastructure Costs (AWS EKS)

```yaml
Monthly Cost Breakdown:
  EKS Control Plane: $72
  
  Worker Nodes (for monitoring):
    t3.medium (2 nodes): $60
    Storage (GP3 100GB): $8
  
  Monitoring Stack Resources:
    Prometheus: 
      CPU: 1 core
      Memory: 2GB
      Storage: 50GB (metrics retention 30d)
    
    Loki:
      CPU: 0.5 core
      Memory: 1GB
      Storage: S3 backend ($23/TB/month)
    
    Grafana:
      CPU: 0.5 core
      Memory: 512MB
      Storage: 10GB
  
  Total: ~$140/month (vs ~$500/month for CloudWatch equivalent)
```

### Cost Optimization Tips

```yaml
Optimization Strategies:
  1. Metrics Cardinality Control:
     - Limit labels to < 10 per metric
     - Use recording rules for expensive queries
     - Drop unnecessary metrics at scrape time
  
  2. Log Volume Management:
     - Structured logging (JSON)
     - Log sampling for verbose services
     - Shorter retention for debug logs
  
  3. Storage Optimization:
     - S3 for Loki (cheaper than EBS)
     - Compression enabled
     - Lifecycle policies for old data
```

## Implementation Guide

### Step 1: Install Helm and Add Repositories

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring
```

### Step 2: Install Prometheus with kube-prometheus-stack

```bash
# Create values file for Prometheus
cat > prometheus-values.yaml <<'EOF'
# Prometheus Configuration
prometheus:
  prometheusSpec:
    retention: 30d
    retentionSize: "45GB"
    
    # Service discovery for your app
    serviceMonitorSelector: {}
    serviceMonitorNamespaceSelector: {}
    podMonitorSelector: {}
    podMonitorNamespaceSelector: {}
    
    # Resources
    resources:
      requests:
        cpu: 500m
        memory: 2Gi
      limits:
        cpu: 2
        memory: 4Gi
    
    # Storage
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    
    # Additional scrape configs for your 3-tier app
    additionalScrapeConfigs:
    - job_name: 'backend-metrics'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - 3-tier-app-eks
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: backend
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: "8000"
      - source_labels: [__address__]
        target_label: __address__
        regex: (.+)
        replacement: ${1}:8000/metrics

# AlertManager Configuration
alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi
    
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 256Mi

# Grafana Configuration
grafana:
  enabled: true
  adminPassword: "Admin123!Secure"
  
  persistence:
    enabled: true
    storageClassName: gp3
    size: 10Gi
  
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  
  # Pre-configured datasources
  sidecar:
    datasources:
      enabled: true
      defaultDatasourceEnabled: true
      uid: prometheus
    dashboards:
      enabled: true
      searchNamespace: ALL
      provider:
        foldersFromFilesStructure: true

# Component monitors
kubeStateMetrics:
  enabled: true
nodeExporter:
  enabled: true
EOF

# Install Prometheus stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-values.yaml \
  --version 51.3.0
```

### Step 3: Install Loki for Log Aggregation

```bash
# Create Loki values file
cat > loki-values.yaml <<'EOF'
loki:
  auth_enabled: false
  
  # Use S3 for storage (cost-effective)
  storage:
    type: s3
    s3:
      endpoint: s3.us-east-1.amazonaws.com
      region: us-east-1
      bucketnames: your-loki-storage-bucket
      insecure: false
      s3forcepathstyle: false
  
  # Schema config
  schema_config:
    configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: s3
      schema: v11
      index:
        prefix: loki_index_
        period: 24h
  
  # Limits
  limits_config:
    enforce_metric_name: false
    reject_old_samples: true
    reject_old_samples_max_age: 168h
    max_entries_limit_per_query: 5000
    retention_period: 720h
  
  # Resources
  resources:
    requests:
      cpu: 250m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 1Gi

# Promtail Configuration (Log shipper)
promtail:
  enabled: true
  
  config:
    clients:
    - url: http://loki:3100/loki/api/v1/push
    
    snippets:
      pipelineStages:
      - docker: {}
      - regex:
          expression: '^(?P<timestamp>\S+)\s+(?P<stream>\S+)\s+(?P<level>\S+)\s+(?P<message>.*)$'
      - labels:
          stream:
          level:
      - timestamp:
          format: RFC3339
          source: timestamp
      
      # Scrape configs for your 3-tier app
      scrapeConfigs: |
        - job_name: kubernetes-pods
          kubernetes_sd_configs:
          - role: pod
          pipeline_stages:
          - docker: {}
          relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: (frontend|backend|postgres-db)
          - source_labels: [__meta_kubernetes_pod_node_name]
            target_label: node_name
          - source_labels: [__meta_kubernetes_namespace]
            target_label: namespace
          - source_labels: [__meta_kubernetes_pod_name]
            target_label: pod
          - source_labels: [__meta_kubernetes_pod_label_app]
            target_label: app
  
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 250m
      memory: 256Mi
EOF

# Install Loki
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --values loki-values.yaml \
  --version 2.9.11
```

### Step 4: Configure Grafana Data Sources

```bash
# Add Loki as datasource to existing Grafana
cat > grafana-datasources.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
  labels:
    grafana_datasource: "1"
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      uid: prometheus
      url: http://prometheus-kube-prometheus-prometheus:9090
      access: proxy
      isDefault: true
      jsonData:
        timeInterval: 30s
    - name: Loki
      type: loki
      uid: loki
      url: http://loki:3100
      access: proxy
      jsonData:
        derivedFields:
        - datasourceUid: prometheus
          matcherRegex: ".*pod=\"([^\"]+)\".*"
          name: TraceID
          url: "$${__value.raw}"
EOF

kubectl apply -f grafana-datasources.yaml
```

### Step 5: Deploy ServiceMonitors for Your 3-Tier App

```yaml
# service-monitors.yaml
---
# Frontend ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: frontend-monitor
  namespace: 3-tier-app-eks
  labels:
    app: frontend
    release: prometheus
spec:
  selector:
    matchLabels:
      app: frontend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
# Backend ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: 3-tier-app-eks
  labels:
    app: backend
    release: prometheus
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
    relabelings:
    - sourceLabels: [__address__]
      targetLabel: __address__
      regex: (.+):(.+)
      replacement: ${1}:8000
---
# PostgreSQL Exporter Deployment and ServiceMonitor
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
  namespace: 3-tier-app-eks
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres-exporter
  template:
    metadata:
      labels:
        app: postgres-exporter
    spec:
      containers:
      - name: postgres-exporter
        image: prometheuscommunity/postgres-exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: DATABASE_URL
        ports:
        - containerPort: 9187
          name: metrics
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-exporter
  namespace: 3-tier-app-eks
  labels:
    app: postgres-exporter
spec:
  selector:
    app: postgres-exporter
  ports:
  - port: 9187
    targetPort: 9187
    name: metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: postgres-monitor
  namespace: 3-tier-app-eks
  labels:
    app: postgres
    release: prometheus
spec:
  selector:
    matchLabels:
      app: postgres-exporter
  endpoints:
  - port: metrics
    interval: 30s
```

## Application Instrumentation

### Backend (Python/Flask) Instrumentation

```python
# backend/app.py - Add Prometheus metrics to Flask
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import psutil

app = Flask(__name__)

# Define metrics
http_requests_total = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

database_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Business metrics
orders_created = Counter(
    'orders_created_total',
    'Total orders created',
    ['payment_method']
)

revenue_total = Counter(
    'revenue_total_dollars',
    'Total revenue in dollars'
)

# Middleware to track metrics
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time.time() - request.start_time
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(elapsed)
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    
    return response

# Metrics endpoint
@app.route('/metrics')
def metrics():
    # Update system metrics
    database_connections.set(get_db_connections())
    
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'backend'
    })

# Example business endpoint with metrics
@app.route('/api/order', methods=['POST'])
def create_order():
    # Your order logic here
    order_data = request.json
    
    # Track business metrics
    orders_created.labels(payment_method=order_data.get('payment_method', 'unknown')).inc()
    revenue_total.inc(order_data.get('total', 0))
    
    return jsonify({'status': 'success', 'order_id': '12345'})

def get_db_connections():
    # Implement your database connection count logic
    return 5  # Example value

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

### Frontend (React) Instrumentation

```javascript
// frontend/src/metrics.js - Browser metrics collection
class MetricsCollector {
  constructor(backendUrl) {
    this.backendUrl = backendUrl;
    this.metrics = {
      pageViews: 0,
      errors: [],
      apiCalls: {},
      performance: {}
    };
    
    this.initializeCollectors();
  }
  
  initializeCollectors() {
    // Page view tracking
    this.trackPageView();
    
    // Error tracking
    window.addEventListener('error', (e) => this.trackError(e));
    window.addEventListener('unhandledrejection', (e) => this.trackError(e));
    
    // Performance tracking
    this.trackPerformance();
    
    // Send metrics every 30 seconds
    setInterval(() => this.sendMetrics(), 30000);
  }
  
  trackPageView() {
    this.metrics.pageViews++;
    
    // Track navigation timing
    if (window.performance && window.performance.timing) {
      const timing = window.performance.timing;
      this.metrics.performance = {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
        loadComplete: timing.loadEventEnd - timing.loadEventStart,
        domInteractive: timing.domInteractive - timing.domLoading,
        firstPaint: this.getFirstPaint()
      };
    }
  }
  
  trackError(error) {
    this.metrics.errors.push({
      message: error.message || error.reason,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      url: window.location.href
    });
  }
  
  trackApiCall(endpoint, duration, status) {
    if (!this.metrics.apiCalls[endpoint]) {
      this.metrics.apiCalls[endpoint] = {
        count: 0,
        totalDuration: 0,
        errors: 0
      };
    }
    
    this.metrics.apiCalls[endpoint].count++;
    this.metrics.apiCalls[endpoint].totalDuration += duration;
    
    if (status >= 400) {
      this.metrics.apiCalls[endpoint].errors++;
    }
  }
  
  getFirstPaint() {
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType('paint');
      const firstPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
      return firstPaint ? firstPaint.startTime : 0;
    }
    return 0;
  }
  
  async sendMetrics() {
    try {
      await fetch(`${this.backendUrl}/api/browser-metrics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...this.metrics,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        })
      });
      
      // Reset certain metrics after sending
      this.metrics.errors = [];
    } catch (error) {
      console.error('Failed to send metrics:', error);
    }
  }
}

// Initialize metrics collector
const metricsCollector = new MetricsCollector(process.env.REACT_APP_BACKEND_URL);

// Export for use in API calls
export const trackApiCall = (endpoint, duration, status) => {
  metricsCollector.trackApiCall(endpoint, duration, status);
};

// Axios interceptor example
import axios from 'axios';

axios.interceptors.request.use(request => {
  request.metadata = { startTime: new Date() };
  return request;
});

axios.interceptors.response.use(
  response => {
    const duration = new Date() - response.config.metadata.startTime;
    trackApiCall(response.config.url, duration, response.status);
    return response;
  },
  error => {
    if (error.config && error.config.metadata) {
      const duration = new Date() - error.config.metadata.startTime;
      trackApiCall(error.config.url, duration, error.response?.status || 0);
    }
    return Promise.reject(error);
  }
);
```

### Database Metrics Configuration

```yaml
# postgres-config.yaml - PostgreSQL configuration for metrics
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: 3-tier-app-eks
data:
  postgresql.conf: |
    # Enable statistics collection
    shared_preload_libraries = 'pg_stat_statements'
    pg_stat_statements.track = all
    pg_stat_statements.max = 10000
    track_io_timing = on
    track_functions = all
    
    # Logging for slow queries
    log_min_duration_statement = 100  # Log queries slower than 100ms
    log_checkpoints = on
    log_connections = on
    log_disconnections = on
    log_lock_waits = on
    log_temp_files = 0
    log_autovacuum_min_duration = 0
    
  queries.yaml: |
    # Custom queries for postgres_exporter
    pg_replication:
      query: "SELECT application_name, state, sync_priority, sync_state FROM pg_stat_replication;"
      metrics:
        - application_name:
            usage: "LABEL"
            description: "Application name"
        - state:
            usage: "LABEL"
            description: "Replication state"
        - sync_priority:
            usage: "GAUGE"
            description: "Synchronous replication priority"
    
    pg_database_size:
      query: "SELECT datname, pg_database_size(datname) as size_bytes FROM pg_database WHERE datistemplate = false;"
      metrics:
        - datname:
            usage: "LABEL"
            description: "Database name"
        - size_bytes:
            usage: "GAUGE"
            description: "Database size in bytes"
```

## Production Concepts

### 1. The Four Golden Signals

```yaml
Golden Signals Implementation:

1. Latency:
   Metric: http_request_duration_seconds
   Query: histogram_quantile(0.95, http_request_duration_seconds_bucket)
   SLO: P95 < 200ms
   Alert: P95 > 500ms for 5 minutes

2. Traffic:
   Metric: http_requests_total
   Query: rate(http_requests_total[5m])
   SLO: Handle 1000 req/s
   Alert: Traffic > 1500 req/s or < 10 req/s

3. Errors:
   Metric: http_requests_total{status=~"5.."}
   Query: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
   SLO: Error rate < 0.1%
   Alert: Error rate > 1% for 5 minutes

4. Saturation:
   Metrics: 
     - container_memory_usage_bytes / container_spec_memory_limit_bytes
     - rate(container_cpu_usage_seconds_total[5m])
   SLO: CPU < 80%, Memory < 90%
   Alert: Resource usage > 90% for 10 minutes
```

### 2. RED Method for Services

```promql
# Rate - Requests per second
sum(rate(http_requests_total{job="backend"}[5m])) by (endpoint)

# Errors - Error rate
sum(rate(http_requests_total{job="backend",status=~"5.."}[5m])) by (endpoint)
/ sum(rate(http_requests_total{job="backend"}[5m])) by (endpoint)

# Duration - Request latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="backend"}[5m])) by (endpoint, le)
)
```

### 3. USE Method for Resources

```promql
# Utilization - CPU usage
100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])))

# Saturation - Memory pressure
rate(node_vmstat_pgmajfault[5m])

# Errors - Node errors
rate(node_network_transmit_errs_total[5m]) + rate(node_network_receive_errs_total[5m])
```

### 4. SLI/SLO/SLA Implementation

```yaml
# slo-config.yaml
apiVersion: sloth.slok.dev/v1
kind: PrometheusServiceLevel
metadata:
  name: backend-slo
  namespace: 3-tier-app-eks
spec:
  service: backend
  labels:
    team: platform
    tier: "1"
  slos:
    - name: requests-availability
      description: "99.9% of requests should be successful"
      objective: 99.9
      sli:
        events:
          error_query: |
            sum(rate(http_requests_total{job="backend",status=~"5.."}[5m]))
          total_query: |
            sum(rate(http_requests_total{job="backend"}[5m]))
      alerting:
        name: BackendAvailability
        page_alert:
          labels:
            severity: critical
        ticket_alert:
          labels:
            severity: warning
    
    - name: requests-latency
      description: "95% of requests should be faster than 200ms"
      objective: 95
      sli:
        events:
          error_query: |
            sum(rate(http_request_duration_seconds_bucket{job="backend",le="0.2"}[5m]))
          total_query: |
            sum(rate(http_request_duration_seconds_count{job="backend"}[5m]))
```

## Dashboards and Alerts

### Production Dashboard JSON

```json
{
  "dashboard": {
    "title": "3-Tier Application Production Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (app)",
            "legendFormat": "{{app}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (app) / sum(rate(http_requests_total[5m])) by (app)",
            "legendFormat": "{{app}}"
          }
        ],
        "type": "graph",
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [0.01],
                "type": "gt"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "name": "High Error Rate",
          "message": "Error rate is above 1%"
        }
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (app, le))",
            "legendFormat": "{{app}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"production\"}",
            "legendFormat": "Active Connections"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Pod Memory Usage",
        "targets": [
          {
            "expr": "sum(container_memory_working_set_bytes{namespace=\"3-tier-app-eks\"}) by (pod) / 1024 / 1024",
            "legendFormat": "{{pod}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Application Logs",
        "targets": [
          {
            "expr": "{namespace=\"3-tier-app-eks\"} |~ \"ERROR|WARN\"",
            "datasource": "Loki"
          }
        ],
        "type": "logs"
      }
    ]
  }
}
```

### Alert Rules Configuration

```yaml
# alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: three-tier-app-alerts
  namespace: monitoring
spec:
  groups:
  - name: application
    interval: 30s
    rules:
    # High Error Rate
    - alert: HighErrorRate
      expr: |
        (sum(rate(http_requests_total{status=~"5.."}[5m])) by (app) 
        / sum(rate(http_requests_total[5m])) by (app)) > 0.01
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High error rate on {{ $labels.app }}"
        description: "{{ $labels.app }} has error rate of {{ $value | humanizePercentage }}"
        runbook: "https://wiki.company.com/runbooks/high-error-rate"
    
    # High Latency
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(http_request_duration_seconds_bucket[5m])) by (app, le)
        ) > 0.5
      for: 10m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High latency on {{ $labels.app }}"
        description: "P95 latency is {{ $value }}s"
    
    # Pod Crash Looping
    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[5m]) > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping"
        description: "Pod has restarted {{ $value }} times in 5 minutes"
    
    # Database Connection Pool Exhaustion
    - alert: DatabaseConnectionPoolExhaustion
      expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Database connection pool nearly exhausted"
        description: "{{ $value | humanizePercentage }} of connections used"
    
    # Disk Space Warning
    - alert: DiskSpaceWarning
      expr: |
        (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Low disk space on node {{ $labels.instance }}"
        description: "Only {{ $value | humanizePercentage }} disk space remaining"
    
    # Memory Pressure
    - alert: MemoryPressure
      expr: |
        (container_memory_working_set_bytes{namespace="3-tier-app-eks"} 
        / container_spec_memory_limit_bytes) > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Memory pressure on {{ $labels.pod }}"
        description: "Pod using {{ $value | humanizePercentage }} of memory limit"
```

### Grafana Dashboard for SLOs

```yaml
# slo-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: slo-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  slo-dashboard.json: |
    {
      "dashboard": {
        "title": "SLO Dashboard",
        "panels": [
          {
            "title": "Error Budget Remaining",
            "type": "stat",
            "targets": [
              {
                "expr": "(1 - (sum(increase(http_requests_total{status=~\"5..\"}[30d])) / sum(increase(http_requests_total[30d])))) / (1 - 0.999) * 100"
              }
            ],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 25},
                {"color": "green", "value": 50}
              ]
            }
          },
          {
            "title": "Current Availability",
            "type": "gauge",
            "targets": [
              {
                "expr": "(1 - sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))) * 100"
              }
            ],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": 99},
                {"color": "yellow", "value": 99.5},
                {"color": "green", "value": 99.9}
              ]
            }
          }
        ]
      }
    }
```

## Troubleshooting

### Common Issues and Solutions

#### 1. High Cardinality Metrics

```bash
# Identify high cardinality metrics
curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | while read metric; do
  echo -n "$metric: "
  curl -s "http://localhost:9090/api/v1/series?match[]=$metric" | jq '.data | length'
done | sort -t: -k2 -n -r | head -20

# Fix: Add relabeling to drop unnecessary labels
# In ServiceMonitor:
relabelings:
- sourceLabels: [__name__]
  regex: 'go_.*'
  action: drop
```

#### 2. Prometheus OOMKilled

```yaml
# Solution: Increase memory and configure external storage
prometheus:
  prometheusSpec:
    resources:
      requests:
        memory: 4Gi
      limits:
        memory: 8Gi
    
    # Use Thanos for long-term storage
    thanos:
      enabled: true
      objectStorageConfig:
        name: thanos-storage
        key: config.yaml
```

#### 3. Slow Queries in Grafana

```promql
# Optimize queries using recording rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: recording-rules
spec:
  groups:
  - name: aggregations
    interval: 30s
    rules:
    - record: app:http_requests:rate5m
      expr: sum(rate(http_requests_total[5m])) by (app)
    
    - record: app:error_rate:ratio5m
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (app)
        / sum(rate(http_requests_total[5m])) by (app)
```

#### 4. Loki Not Showing Logs

```bash
# Check Promtail status
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=100

# Verify Promtail can reach Loki
kubectl exec -n monitoring deploy/promtail -- wget -O- http://loki:3100/ready

# Check Loki ingester
kubectl logs -n monitoring -l app.kubernetes.io/name=loki --tail=100 | grep -i error
```

## Demo Scenarios

### Scenario 1: Simulating High Load

```bash
# deploy-load-generator.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: load-generator
  namespace: 3-tier-app-eks
spec:
  parallelism: 5
  template:
    spec:
      containers:
      - name: load-generator
        image: williamyeh/wrk
        command: ["wrk"]
        args:
        - "-t10"
        - "-c100"
        - "-d300s"
        - "--latency"
        - "http://frontend.3-tier-app-eks.svc.cluster.local"
      restartPolicy: Never

# Deploy and monitor
kubectl apply -f deploy-load-generator.yaml

# Watch metrics in Grafana
# Query: rate(http_requests_total[1m])
```

### Scenario 2: Memory Leak Simulation

```python
# memory-leak.py - Add to backend
import threading
import time

leak_data = []

def create_memory_leak():
    while True:
        # Leak 10MB every 10 seconds
        leak_data.append("x" * 10 * 1024 * 1024)
        time.sleep(10)

# Start leak in background thread
if os.getenv('SIMULATE_MEMORY_LEAK') == 'true':
    threading.Thread(target=create_memory_leak, daemon=True).start()
```

### Scenario 3: Database Slow Query

```sql
-- Create slow query for testing
CREATE OR REPLACE FUNCTION slow_query() RETURNS void AS $$
BEGIN
  PERFORM pg_sleep(5);
  RAISE NOTICE 'Slow query completed';
END;
$$ LANGUAGE plpgsql;

-- Monitor in Grafana
-- Query: pg_stat_statements_mean_exec_time_seconds
```

### Scenario 4: Cascading Failure

```yaml
# chaos-mesh-network-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay
  namespace: 3-tier-app-eks
spec:
  action: delay
  mode: all
  selector:
    namespaces:
    - 3-tier-app-eks
    labelSelectors:
      app: backend
  delay:
    latency: "1000ms"
    jitter: "500ms"
  duration: "5m"
```

## Best Practices Checklist

```yaml
Monitoring Best Practices:
  ✅ Metrics:
    - Use consistent naming conventions
    - Limit cardinality (< 10 labels per metric)
    - Implement the Four Golden Signals
    - Use recording rules for expensive queries
    - Set up federation for multi-cluster
  
  ✅ Logging:
    - Use structured logging (JSON)
    - Include correlation IDs
    - Set appropriate log levels
    - Implement log sampling for high volume
    - Separate application and audit logs
  
  ✅ Alerting:
    - Alert on symptoms, not causes
    - Include runbook links
    - Implement alert grouping
    - Set up escalation policies
    - Test alerts regularly
  
  ✅ Dashboards:
    - Create overview and drill-down dashboards
    - Use consistent color schemes
    - Include SLO tracking
    - Add annotations for deployments
    - Version control dashboard JSON
  
  ✅ Security:
    - Enable RBAC for Prometheus/Grafana
    - Use TLS for all connections
    - Rotate credentials regularly
    - Audit access logs
    - Encrypt data at rest
  
  ✅ Cost Optimization:
    - Implement retention policies
    - Use remote storage for long-term data
    - Optimize cardinality
    - Sample non-critical metrics
    - Right-size monitoring infrastructure
```

## Conclusion

This PLG stack provides:
- 📊 Complete observability for your 3-tier application
- 💰 80% cost reduction vs CloudWatch
- 🚀 Cloud-native architecture
- 🔧 Full control and customization
- 📈 Production-ready monitoring

### Next Steps
1. Implement distributed tracing with Jaeger
2. Add synthetic monitoring with Blackbox exporter
3. Set up GitOps for monitoring configuration
4. Implement SLO tracking with Sloth
5. Add custom business metrics

### Additional Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/)
- [The SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
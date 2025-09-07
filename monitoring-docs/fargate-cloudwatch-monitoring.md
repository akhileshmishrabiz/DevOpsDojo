# EKS Fargate Monitoring with CloudWatch and Fluent Bit

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Cost Analysis](#cost-analysis)
4. [Prerequisites](#prerequisites)
5. [Implementation Steps](#implementation-steps)
6. [Production Concepts](#production-concepts)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Overview

AWS Fargate is a serverless compute engine for containers that removes the need to manage EC2 instances. This guide demonstrates production-level logging and monitoring for EKS Fargate using AWS-native services.

### Why Fargate for Production?

- **No Infrastructure Management**: AWS handles the underlying compute
- **Automatic Scaling**: Pods scale without node management
- **Security**: Enhanced isolation between pods
- **Cost Optimization**: Pay only for resources your pods use

### Monitoring Stack Components

```
┌─────────────────────────────────────────────────────────┐
│                     EKS Fargate Pod                      │
├─────────────────────────────────────────────────────────┤
│  Application Container  │  AWS Fluent Bit Sidecar       │
│  (Your App)            │  (Automatic Log Router)        │
└────────┬───────────────┴────────────┬──────────────────┘
         │                            │
         │ Metrics                    │ Logs
         ▼                            ▼
┌─────────────────┐          ┌─────────────────┐
│ CloudWatch      │          │ CloudWatch Logs  │
│ Container       │          │ (Log Groups)     │
│ Insights        │          └─────────────────┘
└─────────────────┘                   │
         │                            │
         └──────────┬─────────────────┘
                    ▼
         ┌─────────────────────┐
         │  CloudWatch         │
         │  Dashboards &       │
         │  Alarms             │
         └─────────────────────┘
```

## Architecture

### Log Flow Architecture

1. **Application** → Writes to stdout/stderr
2. **Fluent Bit** → Automatically injected by Fargate
3. **CloudWatch Logs** → Centralized storage
4. **CloudWatch Insights** → Query and analysis
5. **CloudWatch Alarms** → Alerting

### Key Components

| Component | Purpose | Automatic in Fargate? |
|-----------|---------|----------------------|
| Fluent Bit | Log collection & routing | ✅ Yes |
| CloudWatch Agent | Metrics collection | ✅ Yes |
| Log Groups | Log organization | ❌ Must create |
| IAM Roles | Permissions | ❌ Must configure |

## Cost Analysis

### Fargate Pricing Components

```yaml
Fargate Costs:
  vCPU: $0.04048 per vCPU per hour
  Memory: $0.004445 per GB per hour
  
CloudWatch Costs:
  Log Ingestion: $0.50 per GB
  Log Storage: $0.03 per GB per month
  Log Insights: $0.005 per GB scanned
  
Example Monthly Cost (Production 3-Tier App):
  Frontend (2 pods, 0.25 vCPU, 0.5GB):
    Compute: 2 * (0.25 * $29.15 + 0.5 * $3.20) = $17.83/month
  
  Backend (2 pods, 0.5 vCPU, 1GB):
    Compute: 2 * (0.5 * $29.15 + 1 * $3.20) = $35.30/month
  
  Database (1 pod, 1 vCPU, 2GB):
    Compute: 1 * (1 * $29.15 + 2 * $3.20) = $35.55/month
  
  Logging (assuming 10GB/day):
    Ingestion: 10 * 30 * $0.50 = $150/month
    Storage: 300GB * $0.03 = $9/month
  
  Total: ~$248/month
```

### Cost Optimization Strategies

1. **Log Filtering**: Filter unnecessary logs at source
2. **Log Retention**: Set appropriate retention periods
3. **Sampling**: Sample verbose logs in non-production
4. **Compression**: Use structured logging for better compression

## Prerequisites

```bash
# Required tools
aws --version          # AWS CLI v2.x
kubectl version        # kubectl 1.24+
eksctl version         # eksctl 0.150+

# Required AWS permissions
- eks:CreateFargateProfile
- iam:CreateRole
- logs:CreateLogGroup
- logs:PutRetentionPolicy
```

## Implementation Steps

### Step 1: Create EKS Cluster with Fargate Profile

```bash
# Create cluster with Fargate
eksctl create cluster \
  --name production-fargate \
  --region us-east-1 \
  --fargate \
  --version 1.28

# Or add Fargate profile to existing cluster
eksctl create fargateprofile \
  --cluster production-fargate \
  --name fp-default \
  --namespace default \
  --namespace kube-system
```

### Step 2: Configure IAM Role for Fargate Logging

```bash
# Create IAM policy for CloudWatch Logs
cat > fargate-logging-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF

# Create the policy
aws iam create-policy \
  --policy-name eks-fargate-logging-policy \
  --policy-document file://fargate-logging-policy.json

# Attach to Fargate pod execution role
FARGATE_PROFILE_NAME=fp-default
CLUSTER_NAME=production-fargate

# Get the role ARN
ROLE_ARN=$(aws eks describe-fargate-profile \
  --cluster-name $CLUSTER_NAME \
  --fargate-profile-name $FARGATE_PROFILE_NAME \
  --query 'fargateProfile.podExecutionRoleArn' \
  --output text)

ROLE_NAME=$(echo $ROLE_ARN | cut -d/ -f2)

# Attach the policy
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/eks-fargate-logging-policy
```

### Step 3: Create CloudWatch Log Groups

```bash
# Create log groups for each namespace
aws logs create-log-group --log-group-name /aws/eks/production-fargate/application
aws logs create-log-group --log-group-name /aws/eks/production-fargate/system

# Set retention policy (30 days)
aws logs put-retention-policy \
  --log-group-name /aws/eks/production-fargate/application \
  --retention-in-days 30
```

### Step 4: Configure Fluent Bit ConfigMap

```yaml
# fluent-bit-config.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aws-observability
  labels:
    aws-observability: enabled
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-logging
  namespace: aws-observability
data:
  output.conf: |
    [OUTPUT]
        Name cloudwatch_logs
        Match *
        region us-east-1
        log_group_name /aws/eks/production-fargate/application
        log_stream_prefix ${HOSTNAME}-
        auto_create_group true
        log_retention_days 30
  
  filters.conf: |
    [FILTER]
        Name parser
        Match *
        Key_Name log
        Parser json
        Reserve_Data True
    
    [FILTER]
        Name kubernetes
        Match kube.*
        Merge_Log On
        Keep_Log Off
        Buffer_Size 0
        Kube_Meta_Cache_TTL 300s
  
  parsers.conf: |
    [PARSER]
        Name json
        Format json
        Time_Key timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%LZ
        Time_Keep On
```

### Step 5: Deploy Sample Application with Logging

```yaml
# sample-app-with-logging.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
      annotations:
        # Force Fargate
        eks.amazonaws.com/compute-type: fargate
    spec:
      containers:
      - name: app
        image: nginx:latest
        env:
        - name: LOG_LEVEL
          value: "info"
        - name: STRUCTURED_LOGGING
          value: "true"
        resources:
          requests:
            cpu: 256m
            memory: 512Mi
          limits:
            cpu: 512m
            memory: 1024Mi
        # Structured logging example
        command: ["/bin/sh"]
        args: 
        - -c
        - |
          while true; do
            echo '{"timestamp":"'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'","level":"info","message":"Application heartbeat","pod":"'$HOSTNAME'","version":"1.0.0"}'
            sleep 10
          done
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
spec:
  selector:
    app: sample-app
  ports:
  - port: 80
    targetPort: 80
```

### Step 6: Query Logs with CloudWatch Insights

```sql
-- Find all errors in the last hour
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100

-- Application performance metrics
fields @timestamp, responseTime, statusCode
| filter @logStream like /backend/
| stats avg(responseTime) as avg_response,
        max(responseTime) as max_response,
        count(*) as request_count
  by bin(5m)

-- Pod restart analysis
fields @timestamp, kubernetes.pod_name, @message
| filter @message like /Started container/
| stats count() as restart_count by kubernetes.pod_name
| sort restart_count desc
```

### Step 7: Create CloudWatch Dashboard

```python
# create-dashboard.py
import boto3
import json

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

dashboard_body = {
    "widgets": [
        {
            "type": "log",
            "properties": {
                "query": "SOURCE '/aws/eks/production-fargate/application' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
                "region": "us-east-1",
                "title": "Recent Errors",
                "queryLanguage": "kusto"
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    [ "ECS/ContainerInsights", "PodCpuUtilization", { "stat": "Average" } ],
                    [ ".", "PodMemoryUtilization", { "stat": "Average" } ]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Pod Resource Utilization"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='FargateMonitoring',
    DashboardBody=json.dumps(dashboard_body)
)
```

### Step 8: Configure Alarms

```yaml
# cloudwatch-alarms.yaml
apiVersion: cloudwatch.aws.amazon.com/v1alpha1
kind: Alarm
metadata:
  name: high-error-rate
spec:
  alarmDescription: "Alert when error rate is high"
  metricName: ErrorCount
  namespace: ApplicationMetrics
  statistic: Sum
  period: 300
  evaluationPeriods: 2
  threshold: 10
  comparisonOperator: GreaterThanThreshold
  alarmActions:
    - arn:aws:sns:us-east-1:123456789012:alerts-topic
```

## Production Concepts

### 1. Log Aggregation Patterns

```yaml
Pattern Types:
  Structured Logging:
    Format: JSON
    Benefits: Easy parsing, rich metadata
    Example: {"level":"error","msg":"Database connection failed","timestamp":"2024-01-15T10:00:00Z"}
  
  Correlation IDs:
    Purpose: Track requests across services
    Implementation: X-Request-ID header
    Example: {"request_id":"abc123","service":"backend","action":"user_login"}
  
  Log Levels:
    DEBUG: Detailed diagnostic info
    INFO: General informational messages
    WARN: Warning messages
    ERROR: Error events
    FATAL: Critical failures
```

### 2. Performance Considerations

```yaml
Optimization Techniques:
  Buffering:
    flush_interval: 5s
    buffer_size: 10MB
    
  Batching:
    batch_size: 100
    max_batch_time: 10s
    
  Sampling:
    debug_logs: 10%  # Sample 10% of debug logs
    info_logs: 100%   # Keep all info logs
```

### 3. Security Best Practices

```yaml
Security Measures:
  PII Redaction:
    - Credit card numbers
    - Social security numbers
    - Email addresses (optional)
  
  Encryption:
    At Rest: AES-256
    In Transit: TLS 1.2+
  
  Access Control:
    - IAM roles for service accounts
    - Least privilege principle
    - Audit logging for access
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Logs Not Appearing in CloudWatch

```bash
# Check Fluent Bit configuration
kubectl get configmap aws-logging -n aws-observability -o yaml

# Verify IAM permissions
aws iam get-role-policy --role-name $ROLE_NAME --policy-name eks-fargate-logging-policy

# Check pod annotations
kubectl describe pod <pod-name> | grep -A5 Annotations
```

#### 2. High CloudWatch Costs

```bash
# Analyze log volume
aws logs describe-log-streams \
  --log-group-name /aws/eks/production-fargate/application \
  --order-by LastEventTime \
  --descending \
  --query 'logStreams[0:5].[logStreamName, storedBytes]'

# Set up metric filter for cost monitoring
aws logs put-metric-filter \
  --log-group-name /aws/eks/production-fargate/application \
  --filter-name BytesLogged \
  --filter-pattern '[...]' \
  --metric-transformations \
    metricName=BytesLogged,metricNamespace=LogMetrics,metricValue=$.bytes
```

#### 3. Missing Container Insights Metrics

```bash
# Enable Container Insights
aws eks update-cluster-config \
  --name production-fargate \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Verify Container Insights is enabled
aws eks describe-cluster \
  --name production-fargate \
  --query 'cluster.logging'
```

## Best Practices

### 1. Structured Logging Format

```python
# Python example with structured logging
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'service': 'backend',
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'pod_name': os.getenv('HOSTNAME'),
            'trace_id': getattr(record, 'trace_id', None)
        }
        return json.dumps(log_obj)

# Configure logger
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User login successful", extra={'trace_id': 'abc123', 'user_id': 'user456'})
```

### 2. Cost Optimization Strategies

```yaml
Log Retention Policies:
  Production:
    Hot (CloudWatch): 7 days
    Warm (S3): 30 days
    Cold (Glacier): 1 year
  
  Staging:
    Hot (CloudWatch): 3 days
    Archive (S3): 14 days
  
  Development:
    Hot (CloudWatch): 1 day
    No archive

Log Filtering Rules:
  - Drop debug logs in production
  - Sample info logs (10%)
  - Keep all warn/error logs
  - Aggregate similar messages
```

### 3. Monitoring SLIs and SLOs

```yaml
Service Level Indicators (SLIs):
  Availability:
    Metric: Successful requests / Total requests
    Target (SLO): 99.9%
    
  Latency:
    Metric: P95 response time
    Target (SLO): < 200ms
    
  Error Rate:
    Metric: 5xx errors / Total requests
    Target (SLO): < 0.1%

Alert Thresholds:
  Critical: SLO breach
  Warning: 80% of SLO
  Info: 50% of SLO
```

### 4. Disaster Recovery

```yaml
Backup Strategy:
  Logs:
    - Export to S3 daily
    - Cross-region replication
    - 90-day retention
  
  Dashboards:
    - Export as CloudFormation
    - Version control in Git
  
  Alarms:
    - Infrastructure as Code
    - Terraform/CloudFormation
```

## Demo Scenarios

### Scenario 1: Debugging Application Crash

```bash
# 1. Identify crashing pods
kubectl get pods --all-namespaces | grep -E "CrashLoopBackOff|Error"

# 2. Query CloudWatch for crash logs
aws logs filter-log-events \
  --log-group-name /aws/eks/production-fargate/application \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s000) \
  --query 'events[*].[timestamp,message]' \
  --output table

# 3. Get detailed pod events
kubectl describe pod <pod-name> | tail -20
```

### Scenario 2: Performance Bottleneck Analysis

```sql
-- CloudWatch Insights query for slow requests
fields @timestamp, duration, endpoint, status_code
| filter duration > 1000
| stats count() as slow_requests, avg(duration) as avg_duration by endpoint
| sort slow_requests desc
```

### Scenario 3: Cost Analysis

```python
# analyze_costs.py
import boto3
from datetime import datetime, timedelta

logs_client = boto3.client('logs')
cloudwatch = boto3.client('cloudwatch')

# Get log group sizes
response = logs_client.describe_log_groups()
for lg in response['logGroups']:
    size_bytes = lg.get('storedBytes', 0)
    size_gb = size_bytes / (1024**3)
    monthly_cost = size_gb * 0.03  # $0.03 per GB
    print(f"{lg['logGroupName']}: {size_gb:.2f} GB (${monthly_cost:.2f}/month)")
```

## Conclusion

This Fargate monitoring setup provides:
- ✅ Zero infrastructure management
- ✅ Automatic scaling
- ✅ Production-grade logging
- ✅ Cost-optimized for small to medium workloads
- ✅ AWS-native integration

### Next Steps
1. Implement application-level metrics
2. Add distributed tracing with X-Ray
3. Set up automated remediation
4. Create runbooks for common issues

### Resources
- [AWS Fargate Pricing](https://aws.amazon.com/fargate/pricing/)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
# DevOpsDojo Infrastructure

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Infrastructure Components](#infrastructure-components)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Deployment Guide](#deployment-guide)
- [Configuration Details](#configuration-details)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## 🎯 Overview

This Terraform infrastructure provisions a complete AWS environment for the DevOpsDojo project, featuring:
- **Amazon EKS** cluster with managed node groups
- **VPC** with public and private subnets across multiple availability zones
- **RDS PostgreSQL** database with encryption
- **GitHub OIDC** integration for CI/CD
- **KMS** encryption for secrets and database
- **Secrets Manager** for secure credential storage

## 🏗️ Architecture Diagram

```ascii
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   AWS Cloud (ap-south-1)                            │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                            VPC (10.0.0.0/16)                                 │  │
│  │                                                                              │  │
│  │  ┌─────────────────────────────────────┐  ┌─────────────────────────────┐  │  │
│  │  │   Public Subnet 1 (10.0.101.0/24)   │  │  Public Subnet 2            │  │  │
│  │  │   AZ: ap-south-1a                   │  │  (10.0.102.0/24)            │  │  │
│  │  │                                     │  │  AZ: ap-south-1b            │  │  │
│  │  │   ┌────────────────┐               │  │                             │  │  │
│  │  │   │  NAT Gateway    │               │  │                             │  │  │
│  │  │   └────────┬───────┘               │  │                             │  │  │
│  │  └─────────────┼───────────────────────┘  └─────────────────────────────┘  │  │
│  │                │                                                            │  │
│  │  ┌─────────────▼───────────────────────────────────────────────────────┐  │  │
│  │  │                    Private Subnets (EKS Worker Nodes)                │  │  │
│  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │  │  │
│  │  │  │  10.0.1.0/24     │  │  10.0.2.0/24     │  │  10.0.3.0/24     │  │  │  │
│  │  │  │  ap-south-1a     │  │  ap-south-1b     │  │  ap-south-1a     │  │  │  │
│  │  │  └──────────────────┘  └──────────────────┘  └──────────────────┘  │  │  │
│  │  │  ┌──────────────────┐                                               │  │  │
│  │  │  │  10.0.4.0/24     │                                               │  │  │
│  │  │  │  ap-south-1b     │                                               │  │  │
│  │  │  └──────────────────┘                                               │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                              │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Database Subnets (RDS)                         │  │  │
│  │  │  ┌──────────────────┐  ┌──────────────────┐                      │  │  │
│  │  │  │  10.0.5.0/24     │  │  10.0.6.0/24     │                      │  │  │
│  │  │  │  ap-south-1a     │  │  ap-south-1b     │                      │  │  │
│  │  │  └──────────────────┘  └──────────────────┘                      │  │  │
│  │  └───────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          Amazon EKS Cluster                                  │  │
│  │                                                                              │  │
│  │  Cluster Name: main-dev-cluster                                              │  │
│  │  Version: 1.31                                                               │  │
│  │                                                                              │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                    Managed Node Group                              │    │  │
│  │  │  • Name: example                                                   │    │  │
│  │  │  • Instance Type: t3.medium                                        │    │  │
│  │  │  • AMI: AL2023_x86_64_STANDARD                                     │    │  │
│  │  │  • Min: 1, Max: 3, Desired: 2                                      │    │  │
│  │  └────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                              │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐    │  │
│  │  │                         Add-ons                                     │    │  │
│  │  │  • CoreDNS                                                          │    │  │
│  │  │  • EKS Pod Identity Agent                                           │    │  │
│  │  │  • kube-proxy                                                       │    │  │
│  │  │  • VPC CNI                                                          │    │  │
│  │  └────────────────────────────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                       RDS PostgreSQL Database                                │  │
│  │                                                                              │  │
│  │  • Engine: PostgreSQL 14.15                                                  │  │
│  │  • Instance Class: db.t3.micro                                               │  │
│  │  • Storage: 30GB (gp3) with autoscaling to 50GB                             │  │
│  │  • Encryption: KMS                                                           │  │
│  │  • Multi-AZ: No (can be enabled for production)                             │  │
│  │  • Automated Backups: 2 days retention                                      │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                    Security & Identity Components                            │  │
│  │                                                                              │  │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐    │  │
│  │  │  GitHub OIDC    │  │  Secrets Manager │  │  KMS Encryption Keys    │    │  │
│  │  │  Provider       │  │  (DB Credentials)│  │  (RDS & Secrets)        │    │  │
│  │  └─────────────────┘  └──────────────────┘  └─────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
infra/
├── modules/                    # Reusable Terraform modules
│   ├── network/                # VPC networking module (currently unused)
│   │   ├── main.tf
│   │   ├── output.tf
│   │   └── variables.tf
│   └── oidc/                   # GitHub OIDC authentication module
│       ├── main.tf
│       ├── output.tf
│       └── variables.tf
├── data.tf                     # Data sources (AZs, region, account info)
├── eks.tf                      # EKS cluster configuration
├── network.tf                  # VPC and networking setup
├── oidc.tf                     # OIDC configuration (currently commented)
├── output.tf                   # Terraform outputs
├── rds.tf                      # RDS PostgreSQL database
├── variables.tf                # Variable definitions
├── version.tf                  # Terraform and provider versions
└── README.md                   # This file
```

## 🔧 Infrastructure Components

### 1. **Networking (network.tf)**
- **VPC**: `10.0.0.0/16` CIDR block
- **Public Subnets**: 2 subnets for load balancers and NAT gateway
  - `10.0.101.0/24` (ap-south-1a)
  - `10.0.102.0/24` (ap-south-1b)
- **Private Subnets**: 4 subnets for EKS worker nodes
  - `10.0.1.0/24`, `10.0.2.0/24`, `10.0.3.0/24`, `10.0.4.0/24`
- **NAT Gateway**: Single NAT for cost optimization
- **DNS**: Enabled hostnames and DNS support
- **Subnet Tags**: Kubernetes tags for ELB and internal-ELB discovery

### 2. **EKS Cluster (eks.tf)**
- **Module**: terraform-aws-modules/eks/aws v20.x
- **Cluster Version**: Kubernetes 1.31
- **Node Group**:
  - Type: Managed node group
  - AMI: Amazon Linux 2023
  - Instance Types: t3.medium
  - Scaling: Min 1, Max 3, Desired 2
- **Add-ons**:
  - CoreDNS (cluster DNS)
  - EKS Pod Identity Agent
  - kube-proxy (network proxy)
  - VPC CNI (container networking)
- **Access**: Public endpoint enabled
- **Admin Permissions**: Creator has admin access

### 3. **Database (rds.tf)**
- **Engine**: PostgreSQL 14.15
- **Instance**: db.t3.micro
- **Storage**: 
  - 30GB initial (gp3 type)
  - Auto-scaling up to 50GB
- **Security**:
  - KMS encryption at rest
  - Private subnets only
  - Security group allows port 5432
- **Backups**: 2-day retention period
- **Credentials**: Stored in AWS Secrets Manager

### 4. **Security Components**

#### KMS (rds.tf)
- Encryption key for RDS and Secrets Manager
- 7-day deletion window
- Aliased as `alias/{environment}-rds-kms-key`

#### Secrets Manager (rds.tf)
- Stores database connection string
- Format: `postgresql://username:password@endpoint:port/dbname`
- KMS encrypted
- 7-day recovery window

#### Security Groups
- **RDS Security Group**: Allows PostgreSQL (5432) from VPC
- **EKS Security Groups**: Managed by EKS module

### 5. **GitHub OIDC Integration (oidc.tf - currently disabled)**
- IAM role for GitHub Actions
- Permissions for EKS and ECR operations
- Trust relationship with GitHub identity provider

## 📋 Prerequisites

1. **Tools Required**:
   ```bash
   # Terraform CLI
   terraform >= 1.5.0
   
   # AWS CLI
   aws-cli >= 2.0
   
   # kubectl (for EKS management)
   kubectl >= 1.31
   ```

2. **AWS Permissions**:
   - VPC creation and management
   - EKS cluster creation
   - RDS database creation
   - IAM role and policy management
   - KMS key creation
   - Secrets Manager access

3. **Environment Setup**:
   ```bash
   # Configure AWS credentials
   aws configure
   
   # Set AWS region
   export AWS_REGION=ap-south-1
   ```

## 🚀 Deployment Guide

### Step 1: Initialize Terraform
```bash
cd infra/
terraform init -upgrade
```

### Step 2: Review Variables
Edit `variables.tf` or create `terraform.tfvars`:
```hcl
# terraform.tfvars
aws_region   = "ap-south-1"
environment  = "dev"
prefix       = "main"
project_name = "DevOpsDojo"
```

### Step 3: Plan Deployment
```bash
terraform plan -out=tfplan
```

### Step 4: Apply Infrastructure
```bash
terraform apply tfplan
```

### Step 5: Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig --region ap-south-1 --name main-dev-cluster

# Verify connection
kubectl get nodes
```

### Step 6: Retrieve Database Credentials
```bash
# Get secret from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id db/main-dev-db \
  --query SecretString \
  --output text
```

## ⚙️ Configuration Details

### Variable Definitions

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS deployment region | ap-south-1 |
| `environment` | Environment name | dev |
| `prefix` | Resource name prefix | main |
| `project_name` | Project identifier | DevOpsDojo |
| `github_repositories` | GitHub repos for OIDC | akhileshmishrabiz/DevOpsDojo |

### Database Configuration

| Parameter | Value |
|-----------|-------|
| Allocated Storage | 30 GB |
| Max Storage | 50 GB |
| Engine Version | PostgreSQL 14.15 |
| Instance Class | db.t3.micro |
| Backup Retention | 2 days |
| Database Name | postgres |
| Username | postgres |

### Network Configuration

| Subnet Type | CIDR Range | Purpose |
|-------------|------------|---------|
| Public | 10.0.101.0/24 - 10.0.102.0/24 | Load balancers, NAT |
| Private (EKS) | 10.0.1.0/24 - 10.0.4.0/24 | Worker nodes |
| Private (RDS) | 10.0.5.0/24 - 10.0.6.0/24 | Database |

## 🔍 Troubleshooting

### EKS Node Connection Issues

**Problem**: Nodes not joining the cluster

**Solution Applied**: Added required Kubernetes tags to subnets:
```hcl
public_subnet_tags = {
  "kubernetes.io/cluster/${cluster-name}" = "shared"
  "kubernetes.io/role/elb"                = "1"
}

private_subnet_tags = {
  "kubernetes.io/cluster/${cluster-name}" = "shared"
  "kubernetes.io/role/internal-elb"       = "1"
}
```

### Common Commands

```bash
# Check EKS cluster status
aws eks describe-cluster --name main-dev-cluster

# View node status
kubectl get nodes -o wide

# Check pod status
kubectl get pods --all-namespaces

# View EKS add-ons
aws eks list-addons --cluster-name main-dev-cluster

# Database connectivity test
psql postgresql://username:password@endpoint:5432/postgres
```

### Terraform State Issues

```bash
# Refresh state
terraform refresh

# Import existing resources
terraform import module.eks.aws_eks_cluster.this main-dev-cluster

# Force unlock state
terraform force-unlock <lock-id>
```

## 🔒 Security Considerations

1. **Network Security**:
   - RDS in private subnets only
   - Single NAT gateway (consider multiple for production)
   - Security groups follow least privilege

2. **Data Security**:
   - KMS encryption for RDS and secrets
   - Secrets Manager for credential management
   - No hardcoded passwords

3. **Access Control**:
   - EKS RBAC for cluster access
   - IAM roles for service accounts (IRSA)
   - GitHub OIDC for CI/CD (when enabled)

4. **Recommendations**:
   - Enable RDS Multi-AZ for production
   - Implement VPC Flow Logs
   - Enable GuardDuty for threat detection
   - Regular security group audits
   - Enable AWS Config for compliance

## 📊 Cost Optimization

Current setup is optimized for development:
- Single NAT gateway (saves ~$45/month per additional NAT)
- t3.medium instances for EKS nodes
- db.t3.micro for RDS
- Minimal backup retention

For production, consider:
- Multiple NAT gateways for HA
- Reserved instances for predictable workloads
- Spot instances for non-critical workloads
- S3 lifecycle policies for logs

## 🔄 Maintenance

### Regular Tasks
1. Update EKS cluster version (every 3-4 months)
2. Update EKS add-ons
3. Rotate database passwords
4. Review and update security groups
5. Monitor costs and optimize

### Backup Strategy
- RDS automated backups: 2 days
- Consider implementing:
  - EBS snapshots for persistent volumes
  - S3 backup for application data
  - Cross-region backup for DR

## 📝 License

This infrastructure code is part of the DevOpsDojo project.

## 🤝 Contributing

1. Create feature branch
2. Test changes in dev environment
3. Update documentation
4. Submit pull request

## 📞 Support

For issues or questions:
- Create an issue in the repository
- Contact the DevOps team

---
*Last Updated: 2025*
*Terraform Version: >= 1.5.0*
*AWS Provider: ~> 5.0*
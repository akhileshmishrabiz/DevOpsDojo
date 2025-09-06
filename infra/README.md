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

| Subnet Type | CIDR Range | Purpose | Internet Access |
|-------------|------------|---------|-----------------|
| Public | 10.0.101.0/24 - 10.0.102.0/24 | NAT Gateway, Load balancers | ✅ Direct |
| Private (EKS) | 10.0.1.0/24 - 10.0.4.0/24 | Worker nodes, Pods | ⚠️ Via NAT Gateway |
| Private (RDS) | 10.0.5.0/24 - 10.0.6.0/24 | Database | ❌ None |

### **🌐 Public Subnets Usage**

**What Lives in Public Subnets:**
1. **NAT Gateway** 🌉 - Provides internet access for private subnets
2. **Load Balancers** ⚖️ - When you create Kubernetes `LoadBalancer` services
3. **Bastion Hosts** 🏰 - If you need SSH access (optional)

**What's NOT in Public Subnets:**
- ❌ EKS Worker Nodes (security - they're in private subnets)
- ❌ Application Pods (they run on private nodes)
- ❌ Databases (they're in dedicated database subnets)

**Subnet Architecture:**
```
Internet
    │
    ▼
┌─────────────────┐
│ Public Subnets  │  ← Internet-facing resources
│ - NAT Gateway   │  ← Provides outbound internet for private subnets
│ - Load Balancers│  ← For external services (when created)
└─────────────────┘
    │ (outbound only)
    ▼
┌─────────────────┐
│ Private Subnets │  ← Secure, no direct internet access
│ - EKS Nodes     │  ← Worker nodes run here
│ - Application   │  ← Your pods run here
│   Pods          │
└─────────────────┘
    │ (database connections)
    ▼
┌─────────────────┐
│ Database Subs   │  ← Most secure, completely isolated
│ - RDS Postgres  │
└─────────────────┘
```

### **🌉 Why NAT Gateway is Essential**

**The Problem Without NAT Gateway:**
```
❌ WITHOUT NAT:
┌─────────────────┐    
│ Private Subnets │    ← EKS Nodes here
│ (EKS Nodes)     │    
│ - No Internet   │    ← Can't download Docker images!
│ - Can't update  │    ← Can't install packages!
│ - Isolated      │    ← Can't reach AWS APIs!
└─────────────────┘    
```

**NAT Gateway Solution:**
```
✅ WITH NAT:
┌─────────────────┐    ┌─────────────────┐
│ Public Subnet   │    │ Private Subnets │
│                 │    │ (EKS Nodes)     │
│ ┌─────────────┐ │    │                 │
│ │ NAT Gateway │◄────┤ Outbound Traffic│
│ │ + Internet  │ │    │ - Docker images │
│ │   Gateway   │ │    │ - Package updates│
│ │             │ │    │ - AWS API calls │
│ └─────────────┘ │    │                 │
└─────────────────┘    └─────────────────┘
```

**What EKS Nodes Need NAT For:**
- 🐳 **Container Images**: Pull from Docker Hub, Amazon ECR, Google Container Registry
- 📦 **Package Updates**: Security patches, system updates
- ☁️ **AWS API Access**: Register with EKS cluster, assume IAM roles, create EBS volumes
- 🌐 **Application Traffic**: Outbound HTTP/HTTPS calls from your applications

**Our NAT Configuration:**
```hcl
enable_nat_gateway = true   # Enable NAT functionality
single_nat_gateway = true   # Cost optimization: $45/month vs $90/month for multi-AZ
```

**Cost vs Availability:**
- **Single NAT** (our choice): ~$45/month, single point of failure
- **Multi-AZ NAT** (production): ~$90/month, high availability

**Security Benefits:**
- **Outbound Only**: Private subnets can reach internet
- **No Inbound**: Internet cannot initiate connections to EKS nodes
- **Firewall**: NAT Gateway acts as a security barrier

### **🗺️ EKS Access Management: aws-auth vs Access Entries**

**Our Setup Uses:** ✅ **Access Entries** (modern approach)

**What is aws-auth ConfigMap?**
The `aws-auth` ConfigMap was the **legacy way** to manage EKS cluster access. It's a Kubernetes ConfigMap that maps AWS IAM users/roles to Kubernetes permissions.

**Legacy aws-auth Method (we DON'T use this):**
```yaml
# This is what we DON'T use
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::account:role/NodeInstanceRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
  mapUsers: |
    - userarn: arn:aws:iam::account:user/admin-user
      username: admin
      groups:
        - system:masters
```

**Modern Access Entries (what we DO use):**
```bash
# This is what we use via AWS API
aws eks create-access-entry \
  --cluster-name main-dev-cluster \
  --principal-arn arn:aws:iam::account:user/admin-user \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name main-dev-cluster \
  --principal-arn arn:aws:iam::account:user/admin-user \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy
```

**Comparison:**

| Feature | aws-auth ConfigMap | Access Entries |
|---------|-------------------|----------------|
| **Method** | Manual YAML editing | AWS API managed |
| **UI Support** | ❌ No AWS Console support | ✅ Full Console integration |
| **Error Handling** | ❌ Easy to break cluster access | ✅ API validation prevents errors |
| **Management** | ❌ kubectl edit configmap | ✅ AWS CLI/Console/Terraform |
| **Version Support** | ✅ All EKS versions | ✅ EKS 1.23+ (current) |
| **Our Choice** | ❌ Legacy, not used | ✅ Modern, actively used |

**Why We Chose Access Entries:**
- **Safer**: API validation prevents breaking cluster access
- **Integrated**: Works seamlessly with AWS Console
- **Future-proof**: AWS recommended approach
- **Easier**: No manual YAML editing required

**EKS Module Version Note:**
```hcl
version = "~> 20.0"  # Using v20 to maintain aws-auth compatibility
```
This means our EKS module **supports** aws-auth if needed, but we **actively use** Access Entries instead.

**When You Might See aws-auth:**
- Older EKS clusters (pre-2023)
- Legacy documentation and tutorials
- EKS clusters that haven't migrated to Access Entries
- Some advanced use cases requiring custom group mappings

**Our Access Method Summary:**
1. **Cluster Creator**: Automatically gets admin access (your CLI user)
2. **Additional Users**: Added via Access Entries API
3. **Console Access**: Configured via Access Entries
4. **Service Accounts**: Use IRSA for AWS permissions (not cluster access)

### **🌐 EKS Cluster Endpoint Access: Public vs Private**

**Our Current Setup:** ✅ **Public Endpoint** (development-friendly)

**What "Public vs Private Cluster" Means:**
This is **NOT** about worker node placement (they're always in private subnets). It's about **how you access the Kubernetes API server** (control plane).

#### **EKS Endpoint Access Modes:**

**1. Public Endpoint (Our Current Setup):**
```hcl
# In our eks.tf
cluster_endpoint_public_access = true   # ← API server accessible from internet
```

**Architecture:**
```
Internet                    Your Laptop/CI
    │                           │
    ▼                           ▼
┌─────────────────┐    ┌─────────────────┐
│ EKS API Server  │◄───┤    kubectl      │  ← Works from anywhere
│ (Control Plane) │    │                 │
│ Public IP       │    └─────────────────┘
└─────────────────┘
    │
    ▼ (manages)
┌─────────────────┐
│ Private Subnets │  ← Worker nodes still private & secure!
│ - Worker Nodes  │
│ - Pods          │
└─────────────────┘
```

**2. Private Endpoint Only:**
```hcl
cluster_endpoint_public_access  = false
cluster_endpoint_private_access = true
```

**Architecture:**
```
Internet
    │
    ✗ (blocked)
    
┌─────────────────┐    ┌─────────────────┐
│ VPC Only        │    │ Need Bastion    │
│ EKS API Server  │◄───┤ or VPN to run   │
│ Private IP      │    │ kubectl         │
└─────────────────┘    └─────────────────┘
    │
    ▼ (manages)
┌─────────────────┐
│ Private Subnets │
│ - Worker Nodes  │
│ - Bastion Host  │  ← kubectl only works from here
└─────────────────┘
```

#### **Access Comparison:**

| Feature | Public Endpoint | Private Endpoint | Hybrid |
|---------|----------------|------------------|--------|
| **Internet Access** | ✅ kubectl from anywhere | ❌ No internet access | ✅ kubectl from anywhere |
| **VPC Access** | ✅ Works from VPC | ✅ Works from VPC | ✅ Works from VPC |
| **Bastion Required** | ❌ No | ✅ Yes | ❌ No |
| **CI/CD Friendly** | ✅ Direct access | ⚠️ Needs VPN/tunnel | ✅ Direct access |
| **AWS Console** | ✅ Full functionality | ⚠️ Limited functionality | ✅ Full functionality |
| **Security Level** | Medium | High | Medium-High |
| **Our Setup** | ✅ **Current** | ❌ | ❌ |

#### **How to Check Current Configuration:**

```bash
# Check via AWS CLI
aws eks describe-cluster \
  --name main-dev-cluster \
  --region ap-south-1 \
  --query 'cluster.resourcesVpcConfig.endpointConfig'

# Example output for our setup:
# {
#     "privateAccess": false,
#     "publicAccess": true,
#     "publicAccessCidrs": ["0.0.0.0/0"]
# }
```

#### **Security Considerations:**

**Our Public Endpoint is Still Secure Because:**
Even though accessible from internet, attackers would need:
1. ✅ **Valid AWS Credentials** (IAM authentication)
2. ✅ **EKS Access Entry** (cluster-level authorization)
3. ✅ **Kubernetes RBAC** (resource-level permissions)
4. ✅ **Valid TLS Certificates** (transport security)

```
Internet Attacker
    │
    ▼
┌─────────────────┐
│ EKS API Server  │
│ 🛡️ AWS IAM      │  ← Must authenticate as valid AWS user
│ 🛡️ EKS Access   │  ← Must be granted cluster access
│ 🛡️ K8s RBAC     │  ← Must have specific permissions
│ 🛡️ TLS/mTLS     │  ← Must have valid certificates
└─────────────────┘
```

#### **When to Use Each Mode:**

**Public Endpoint (Our Choice) - Best For:**
- ✅ Development and staging environments
- ✅ Small to medium teams
- ✅ CI/CD pipelines from external services
- ✅ Quick debugging and iteration

**Private Endpoint - Best For:**
- 🏢 High-security enterprise environments
- 🏦 Financial, healthcare, government sectors
- 🔒 Strict compliance requirements (PCI-DSS, HIPAA)
- 🏰 Existing VPN/bastion infrastructure

**Hybrid (Both) - Best For:**
- 🎯 Production with mixed access needs
- 👥 Development team + automated systems
- 🔄 Migration scenarios

#### **To Change Access Mode (If Needed):**

```hcl
# Make it private-only
module "eks" {
  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true
}

# Restrict public access to specific IPs
module "eks" {
  cluster_endpoint_public_access = true
  cluster_endpoint_public_access_cidrs = [
    "203.0.113.0/24",  # Your office network
    "198.51.100.0/32"  # Your home IP
  ]
}
```

**Important:** Worker nodes, pods, and applications always remain in private subnets regardless of endpoint access mode. The endpoint access only affects how you manage the cluster, not where workloads run.

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

### Nodes Show as NotReady - CNI Plugin Not Initialized

**Problem**: EC2 instances are created and visible with `kubectl get nodes` but show `NotReady` status with error:
```
container runtime network not ready: NetworkReady=false 
reason:NetworkPluginNotReady message:Network plugin returns error: 
cni plugin not initialized
```

**Root Cause**: 
This is a **race condition** in the EKS Terraform module where:
1. The EKS cluster is created first
2. Managed node groups are created immediately after cluster becomes `ACTIVE`
3. EKS addons (including VPC CNI) installation happens in parallel but takes longer
4. Nodes boot up and try to join before the CNI plugin is available

**Why Terraform Module Has This Issue**:
- **Implicit Dependencies**: The terraform-aws-modules/eks module doesn't create proper dependencies between node groups and addons
- **AWS API Timing**: EKS cluster status becomes `ACTIVE` before all addons are fully deployed
- **Bootstrap Race**: Node bootstrap process starts before CNI daemonset is running
- **Terraform State Locks**: If `terraform apply` is interrupted, addons may not be installed

**Symptoms**:
- Nodes visible in `kubectl get nodes` but status is `NotReady`
- No pods in `kube-system` namespace or only partial system pods
- `aws eks list-addons` returns empty array `[]`
- Node describe shows CNI network plugin errors

**Immediate Solution**:
```bash
# 1. Check if addons are missing
aws eks list-addons --cluster-name <cluster-name> --region <region>

# 2. Install missing addons manually
aws eks create-addon --cluster-name <cluster-name> --addon-name vpc-cni --region <region>
aws eks create-addon --cluster-name <cluster-name> --addon-name coredns --region <region>
aws eks create-addon --cluster-name <cluster-name> --addon-name kube-proxy --region <region>
aws eks create-addon --cluster-name <cluster-name> --addon-name eks-pod-identity-agent --region <region>

# 3. Wait 2-3 minutes and check nodes
kubectl get nodes -o wide
```

**Prevention in Terraform**:
Add explicit dependencies in your EKS module:
```hcl
# In eks.tf - Add this to prevent race conditions
resource "time_sleep" "wait_for_cluster" {
  depends_on = [module.eks]
  create_duration = "30s"
}

# Or use depends_on in node groups
eks_managed_node_groups = {
  example = {
    # ... node group config
    
    # Force dependency on cluster addons
    depends_on = [
      aws_eks_addon.vpc_cni,
      aws_eks_addon.coredns
    ]
  }
}
```

**Long-term Solution**:
Consider using terraform-aws-modules/eks v21+ which has better addon handling, or implement explicit addon resources with proper dependencies.

### EBS Volume Provisioning Fails - IAM Permissions Missing

**Problem**: PersistentVolumeClaims remain in `Pending` status with error:
```
failed to provision volume with StorageClass: rpc error: code = Internal desc = 
Could not create volume: UnauthorizedOperation: You are not authorized to perform 
this operation. User: arn:aws:sts::account:assumed-role/example-eks-node-group-.../
i-xxx is not authorized to perform: ec2:CreateVolume
```

**Root Cause**: 
The **EBS CSI Driver addon** can be installed successfully, but it requires proper **IAM permissions** to create EBS volumes. The terraform-aws-modules/eks v20.x doesn't automatically configure IRSA (IAM Roles for Service Accounts) for the EBS CSI driver.

**Why This Happens**:
1. **EBS CSI Addon Installed**: `aws eks create-addon --addon-name aws-ebs-csi-driver` succeeds
2. **CSI Pods Running**: EBS CSI controller and node pods are `Running`
3. **Missing IRSA**: EBS CSI service account lacks IAM permissions to call EC2 APIs
4. **Volume Creation Fails**: CSI driver can't create/attach/delete EBS volumes

**Immediate Solutions**:

**Option 1: Configure IRSA for EBS CSI Driver (Recommended)**
```bash
# 1. Get OIDC issuer URL
CLUSTER_NAME="main-dev-cluster"
OIDC_ISSUER=$(aws eks describe-cluster --name $CLUSTER_NAME --region ap-south-1 \
  --query 'cluster.identity.oidc.issuer' --output text)

# 2. Create IAM role for EBS CSI driver
cat <<EOF > ebs-csi-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query 'Account' --output text):oidc-provider/${OIDC_ISSUER#https://}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_ISSUER#https://}:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
          "${OIDC_ISSUER#https://}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# 3. Create the IAM role
aws iam create-role \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --assume-role-policy-document file://ebs-csi-trust-policy.json

# 4. Attach the AWS managed policy
aws iam attach-role-policy \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# 5. Update the addon with the IAM role
aws eks update-addon \
  --cluster-name $CLUSTER_NAME \
  --addon-name aws-ebs-csi-driver \
  --region ap-south-1 \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query 'Account' --output text):role/AmazonEKS_EBS_CSI_DriverRole

# 6. Clean up
rm ebs-csi-trust-policy.json
```

**Option 2: Add EBS Permissions to Node Group Role (Quick Fix)**
```bash
# Get the node group role name
NODE_ROLE_NAME=$(aws eks describe-nodegroup \
  --cluster-name main-dev-cluster \
  --nodegroup-name example \
  --region ap-south-1 \
  --query 'nodegroup.nodeRole' --output text | cut -d'/' -f2)

# Attach EBS CSI policy to node group role
aws iam attach-role-policy \
  --role-name $NODE_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
```

**Verification**:
```bash
# Check EBS CSI driver status
kubectl get pods -n kube-system -l app=ebs-csi-controller

# Test volume creation
kubectl apply -f k8s_stuff/pvc-gp2.yaml
kubectl get pvc test-ebs-pvc-gp2 -w

# Should change from Pending to Bound
```

**Prevention in Terraform**:
Add explicit EBS CSI configuration in your `eks.tf`:
```hcl
# Add to the EKS module
module "eks" {
  # ... existing configuration
  
  # EKS Addons with IRSA
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
      service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn
    }
  }
}

# Add EBS CSI IRSA module
module "ebs_csi_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  role_name             = "ebs-csi"
  attach_ebs_csi_policy = true

  oidc_providers = {
    ex = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}
```

**Common Storage Classes Issues**:
- **GP2 vs GP3**: Default `gp2` storage class uses older EBS driver
- **Encryption**: GP3 storage class includes encryption by default
- **IOPS/Throughput**: GP3 allows custom IOPS and throughput settings
- **Volume Binding**: `WaitForFirstConsumer` delays volume creation until pod scheduling

**Symptoms of Fixed Issue**:
- PVC status changes from `Pending` to `Bound`
- New EBS volume appears in AWS EC2 console
- Pod status changes to `Running` with volume mounted
- Files can be written/read from the persistent volume

## 🚀 Infrastructure Updates & Fixes Applied

### **Production-Ready Configuration Overview**

This infrastructure has been updated with **all critical fixes** to prevent common EKS deployment issues. The configuration now follows AWS best practices and includes comprehensive error prevention.

### **Key Updates Applied:**

#### **1. EKS Configuration (`eks.tf`) - Complete Overhaul**
```hcl
# ✅ IRSA Module for Secure EBS CSI Permissions
module "ebs_csi_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  
  role_name             = "${var.prefix}-${var.environment}-ebs-csi-role"
  attach_ebs_csi_policy = true  # AmazonEBSCSIDriverPolicy via service account
}

# ✅ Proper Addon Configuration with Race Condition Prevention
cluster_addons = {
  vpc-cni = {
    before_compute = true  # Ensures CNI is ready before nodes join
  }
  aws-ebs-csi-driver = {
    service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn  # IRSA
  }
}

# ✅ Backup IAM Permissions on Node Groups
eks_managed_node_group_defaults = {
  iam_role_additional_policies = {
    AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  }
}
```

#### **2. Network Configuration (`network.tf`) - EKS Integration**
```hcl
# ✅ Required EKS Subnet Tags (Already Applied)
public_subnet_tags = {
  "kubernetes.io/cluster/${var.prefix}-${var.environment}-cluster" = "shared"
  "kubernetes.io/role/elb" = "1"
}
private_subnet_tags = {
  "kubernetes.io/cluster/${var.prefix}-${var.environment}-cluster" = "shared"  
  "kubernetes.io/role/internal-elb" = "1"
}
```

#### **3. Enhanced Outputs (`output.tf`) - Complete Monitoring**
- **EKS Information**: Cluster endpoint, ARN, OIDC issuer, certificate data
- **Network Details**: VPC ID, subnet IDs for integration
- **Database Access**: RDS endpoints and secrets manager ARNs
- **IRSA Role**: EBS CSI driver role ARN for troubleshooting
- **kubectl Command**: Ready-to-use cluster access command

#### **4. Testing Infrastructure (`k8s_stuff/`)**
- **Volume Test Manifests**: GP2/GP3 storage classes, PVCs, deployments
- **Automated Testing**: `test-volume.sh` script for volume provisioning verification
- **Documentation**: Complete testing guide and troubleshooting

### **IAM Security Architecture**

Our **layered security model** for EBS volume permissions:

| Security Layer | IAM Role Type | Permissions | Use Case |
|----------------|---------------|-------------|----------|
| 🥇 **Primary** | IRSA Service Account | `AmazonEBSCSIDriverPolicy` | EBS CSI driver pods only |
| 🥈 **Backup** | EKS Node Group | `AmazonEBSCSIDriverPolicy` | Fallback if IRSA fails |
| 🥉 **Default** | EKS Cluster | `AmazonEKSClusterPolicy` | Control plane operations |

**Why This Approach?**
- **Security**: IRSA follows principle of least privilege
- **Reliability**: Backup ensures volume provisioning always works
- **Compliance**: Meets AWS security best practices

### **🔍 Understanding IRSA (IAM Roles for Service Accounts)**

**IRSA** allows **specific pods** to have **specific AWS permissions** without giving those permissions to entire worker nodes.

#### **The Problem IRSA Solves:**

```
❌ WITHOUT IRSA (Node-level permissions):
┌─────────────────────┐
│    Worker Node      │
│ ┌─────────────────┐ │  ← ALL pods inherit 
│ │   Any Pod       │ │    node's IAM permissions
│ │ (nginx, app,    │ │    (security risk!)
│ │  ebs-csi, etc.) │ │
│ └─────────────────┘ │
│ Node IAM Role:      │
│ - EBS permissions   │ ← Every pod can create EBS volumes!
│ - S3 permissions    │ ← Every pod can access S3!
└─────────────────────┘
```

```
✅ WITH IRSA (Pod-level permissions):
┌─────────────────────┐
│    Worker Node      │
│ ┌─────────────────┐ │  ← Only basic node permissions
│ │   Regular Pod   │ │
│ │   (nginx, app)  │ │  ← No AWS permissions
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │  EBS CSI Pod    │ │  ← Gets SPECIFIC permissions
│ │ ServiceAccount: │ │    via service account
│ │ ebs-csi-ctrl-sa │ │
│ └─────────────────┘ │
└─────────────────────┘
          │
          │ IRSA Magic ✨
          ▼
┌─────────────────────┐
│ Dedicated IAM Role  │
│ - ONLY EBS perms    │ ← Only EBS CSI pods get this
│ - No other access   │
└─────────────────────┘
```

#### **How IRSA Works - Components:**

| Component | Purpose | Location |
|-----------|---------|----------|
| **Pod** | Runs the application (EBS CSI driver) | Kubernetes Node |
| **ServiceAccount** | Kubernetes identity for pods | `kube-system` namespace |
| **IAM Role** | AWS permissions (EBS operations) | AWS IAM |
| **OIDC Provider** | Trust broker between EKS and IAM | AWS IAM (linked to EKS) |
| **Trust Policy** | "Which service account can use this role?" | IAM Role configuration |
| **Permission Policy** | "What AWS actions are allowed?" | Attached to IAM Role |

#### **Step-by-Step Flow:**

1. **Pod Declaration**: EBS CSI pod uses `serviceAccountName: ebs-csi-controller-sa`

2. **Service Account Annotation**: 
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: ebs-csi-controller-sa
     annotations:
       eks.amazonaws.com/role-arn: arn:aws:iam::account:role/main-dev-ebs-csi-role
   ```

3. **IAM Role Trust**: Role trusts the specific service account via OIDC
   ```json
   "Condition": {
     "StringEquals": {
       "oidc.eks.region.amazonaws.com:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa"
     }
   }
   ```

4. **Automatic Credentials**: Pod gets AWS credentials via environment variables:
   ```bash
   AWS_ROLE_ARN=arn:aws:iam::account:role/main-dev-ebs-csi-role
   AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
   ```

5. **AWS API Calls**: Pod can now create/attach/delete EBS volumes using these credentials

#### **In Our Configuration:**

```hcl
# This creates the IAM role and service account annotation
module "ebs_csi_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  
  role_name             = "main-dev-ebs-csi-role"
  attach_ebs_csi_policy = true  # Adds AmazonEBSCSIDriverPolicy
  
  oidc_providers = {
    ex = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]  # Only this SA
    }
  }
}

# This tells EKS addon to use the IRSA role
cluster_addons = {
  aws-ebs-csi-driver = {
    service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn  # Links everything
  }
}
```

#### **Benefits of IRSA:**

- 🔒 **Principle of Least Privilege**: Each pod gets only the permissions it needs
- 🎯 **Precise Control**: EBS CSI pods can create volumes, nginx pods cannot
- 📊 **Better Auditing**: CloudTrail shows which specific pod made AWS calls
- 🔄 **Automatic Rotation**: No need to manage long-lived AWS keys
- 🚫 **No Secret Management**: No AWS credentials stored in Kubernetes secrets
- 🛡️ **Defense in Depth**: Multiple layers of security (namespace + service account + IAM)

#### **Why We Also Keep Node-Level Backup:**

```hcl
# Backup permission on node group (fallback)
iam_role_additional_policies = {
  AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
```

This ensures volume provisioning works even if:
- IRSA configuration fails
- Service account annotation is missing  
- OIDC provider has issues
- New EKS versions change IRSA behavior

**Result**: Maximum security (IRSA primary) + maximum reliability (node backup) = Production ready! 🚀

### **AWS Console Can't See EKS Nodes - Access Entry Missing**

**Problem**: You can see the EKS cluster in AWS Console, but when clicking on "Nodes" or "Workloads" tabs, it shows "Access denied" or "Set up access required" message.

**Symptoms**:
- `kubectl get nodes` works fine from CLI
- EKS cluster is visible in AWS Console
- **Nodes tab** shows access denied
- **Workloads tab** shows access denied  
- **Resources tab** shows access denied

**Root Cause**: 
EKS has **two separate permission systems**:
1. **Kubernetes RBAC** (for CLI/kubectl) - ✅ Working
2. **AWS Console Access** (for AWS Console) - ❌ Missing

**Why This Happens**:
- **EKS Security Feature**: Only the cluster creator gets initial access
- **Different AWS Identities**: Console user ≠ CLI user who created cluster
- **Common Scenario**: 
  - CLI uses IAM user `cliuser-akhilesh` (created cluster via Terraform)
  - Console uses root user or different IAM user
  - Result: Console can't access EKS resources

**Solutions**:

**Option 1: Use Same User for Console and CLI (Recommended)**
```bash
# Check which user created the cluster
aws sts get-caller-identity

# Log out of AWS Console and log back in as the same user
```

**Option 2: Add Console User to EKS Access Entries**
```bash
# Get your console user ARN (replace with actual ARN)
CONSOLE_USER_ARN="arn:aws:iam::879381241087:root"  # or specific IAM user

# Add console user to EKS cluster access
aws eks create-access-entry \
  --cluster-name main-dev-cluster \
  --principal-arn $CONSOLE_USER_ARN \
  --type STANDARD \
  --region ap-south-1

# Grant admin permissions
aws eks associate-access-policy \
  --cluster-name main-dev-cluster \
  --principal-arn $CONSOLE_USER_ARN \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --region ap-south-1
```

**Option 3: Update via Terraform (Prevention)**
Add explicit access entries in your `eks.tf`:
```hcl
module "eks" {
  # ... existing configuration
  
  # Access entries for additional users
  access_entries = {
    admin-user = {
      principal_arn = "arn:aws:iam::879381241087:user/admin-user"
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
    
    root-user = {
      principal_arn = "arn:aws:iam::879381241087:root"
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }
}
```

**Security Best Practice**:
- **❌ Don't use root user** for day-to-day operations
- **✅ Create dedicated admin IAM user** for EKS management
- **✅ Use same user** for both CLI and Console access
- **✅ Enable MFA** on admin users

**Verification**:
After applying the fix, refresh AWS Console:
- **Nodes tab**: Should show worker nodes
- **Workloads tab**: Should show running pods  
- **Resources tab**: Should show services and resources

**Common Access Entry Commands**:
```bash
# List current access entries
aws eks list-access-entries --cluster-name main-dev-cluster --region ap-south-1

# Describe specific access entry
aws eks describe-access-entry \
  --cluster-name main-dev-cluster \
  --principal-arn "arn:aws:iam::account:user/username" \
  --region ap-south-1

# Delete access entry (if needed)
aws eks delete-access-entry \
  --cluster-name main-dev-cluster \
  --principal-arn "arn:aws:iam::account:user/username" \
  --region ap-south-1
```

### **Issues Prevented**

✅ **Node Connection Failures** - Proper subnet tags for cluster discovery  
✅ **CNI Race Conditions** - Addon ordering ensures networking is ready  
✅ **Volume Provisioning Failures** - Dual IAM approach (IRSA + node backup)  
✅ **System Pod Failures** - Proper addon installation and dependencies  
✅ **Troubleshooting Difficulties** - Comprehensive outputs and documentation  

### **Version Compatibility**

| Component | Version | Reason |
|-----------|---------|--------|
| **Terraform** | >= 1.5.0 | Compatible with your installation |
| **AWS Provider** | ~> 5.0 | Stable, avoids v6 breaking changes |
| **EKS Module** | ~> 20.0 | v21 removes aws-auth (breaking) |
| **VPC Module** | ~> 5.0 | Compatible with AWS Provider v5 |
| **Kubernetes** | 1.31 | Latest stable, support until 2026 |

### **Files Summary**

| File | Purpose | Key Features |
|------|---------|--------------|
| `eks.tf` | EKS cluster config | IRSA, addon ordering, dependencies |
| `network.tf` | VPC and networking | EKS subnet tags, DNS settings |
| `version.tf` | Provider versions | Compatible constraints |
| `output.tf` | Infrastructure outputs | Cluster info, kubectl command |
| `FIXES_APPLIED.md` | Fix documentation | Complete troubleshooting guide |
| `k8s_stuff/` | Testing resources | Volume provisioning tests |

### **Deployment Verification**

After applying these fixes, verify:
```bash
# 1. All nodes are Ready
kubectl get nodes

# 2. System pods are Running  
kubectl get pods -n kube-system

# 3. EBS CSI driver is active
kubectl get pods -n kube-system -l app=ebs-csi-controller

# 4. Volume provisioning works
kubectl apply -f k8s_stuff/pvc-gp2.yaml
kubectl get pvc -w  # Should show Bound status
```

### **Next Steps for Production**

Consider these additional hardening steps:
- Enable **VPC Flow Logs** for network monitoring
- Implement **AWS Config** for compliance
- Set up **GuardDuty** for threat detection  
- Configure **Multiple NAT Gateways** for high availability
- Enable **RDS Multi-AZ** for database redundancy

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
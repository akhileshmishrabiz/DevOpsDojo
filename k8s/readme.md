# DevOps Learning Platform - EKS Deployment Guide

## Prerequisites
- AWS CLI installed and configured
- kubectl installed and configured
- eksctl installed
- Helm installed
- Docker installed


Install kubectl 

curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl

```bash
curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.30.2/2024-07-12/bin/linux/amd64/kubectl
sha256sum -c kubectl.sha256
openssl sha1 -sha256 kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && cp ./kubectl $HOME/bin/kubectl && export PATH=$HOME/bin:$PATH
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
```

Install eksctl 
```bash
ARCH=amd64
PLATFORM=$(uname -s)_$ARCH

curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz"

# (Optional) Verify checksum
curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_checksums.txt" | grep $PLATFORM | sha256sum --check

tar -xzf eksctl_$PLATFORM.tar.gz -C /tmp && rm eksctl_$PLATFORM.tar.gz

sudo mv /tmp/eksctl /usr/local/bin

```
## Step 1: Clone the Repository and Organize Kubernetes Manifests

```bash
# Clone your repository (assuming you have one)
git clone https://github.com/DevOpsDojo.git
cd DevOpsDojo

```

# create cluster ->

eksctl create cluster --name devopsdozo --region ap-south-1

aws eks list-clusters

# Replace my-cluster with your cluster name from the list-clusters output
export cluster_name=devopsdozo

aws eks update-kubeconfig --name $cluster_name --region ap-south-1

kubectl config get-contexts

kubectl config current-context

kubectl config use-context  demo-cluster

```

## Step 3: Create the RDS PostgreSQL Database

Use UI or run cli 

with details as below 
user: postgres
password: postgrespassword
db name: devopsdozo
once created, not down the endpoint url. we will use this while creating database service

Make sure to:
1. Create a security group that allows inbound traffic on port 5432 from your EKS cluster's VPC
2. Create a DB subnet group that includes subnets in at least two availability zones

## Step 4: Build and Push Docker Images

```bash
# Log in to Amazon ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 879381241087.dkr.ecr.ap-south-1.amazonaws.com

# Create ECR repositories
aws ecr create-repository --repository-name devopsdozo/frontend
aws ecr create-repository --repository-name devopsdozo/backend

# Build and push images
docker build -t 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo/frontend:latest --platform=linux/amd64 ./frontend
docker build -t 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo/backend:latest --platform=linux/amd64  ./backend

docker push 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo/frontend:latest
docker push 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo/backend:latest
```

Replace `163962798700` with your AWS account ID.

## Step 5: Configure ALB Ingress Controller

The AWS Application Load Balancer (ALB) Ingress Controller is required for the ingress resource:

```bash

# resource: https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html
oidc_id=$(aws eks describe-cluster --name $cluster_name --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
echo $oidc_id
# Check if IAM OIDC provider with your cluster’s issuer ID 
aws iam list-open-id-connect-providers | grep $oidc_id | cut -d "/" -f4

# If not, create
eksctl utils associate-iam-oidc-provider --cluster $cluster_name --approve
# or use console
-> To create a provider, go to IAM, choose Add provider.
-> For Provider type, select OpenID Connect.
-> For Provider URL, enter the OIDC provider URL for your cluster.
-> For Audience, enter sts.amazonaws.com.
-> (Optional) Add any tags, for example a tag to identify which cluster is for this provider.
-> Choose Add provider.

# IAM policy for loadbalancder controller -> You only need to create an IAM Role for the AWS Load Balancer Controller once per AWS # account. Check if AmazonEKSLoadBalancerControllerRole 
# Resource https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html

curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.11.0/docs/install/iam_policy.json
aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

eksctl create iamserviceaccount \
  --cluster=$cluster_name \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::879381241087:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install the AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"

# install helm 
brew install helm # (for mac)
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$cluster_name \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set vpcId=vpc-06a34931ca660b90b \
  --set region=ap-south-1

```


## Step 6: Update Database Connection in ConfigMap

Edit the `secrets.yaml` file to update the database connection string:

```yaml
DATABASE_URL: "postgresql://postgres:<strong-password>@devops-learning-db.<your-db-endpoint>.us-west-2.rds.amazonaws.com:5432/devops_learning"
```

Replace `<strong-password>` and `<your-db-endpoint>` with your actual values.

## Step 7: Deploy the Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
# Update the database-service.yaml with database endpoint 
kubectl apply -f k8s/database-service.yaml

# this job is only run when there is a change in schema or the first time while deployig the app
kubectl apply -f k8s/migration_job.yaml  # it run once 

# start the backnd and frontend services
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/horizontal-pod-autoscaler.yaml

# Verify deployments
kubectl get pods -n devopsdozo
kubectl get svc -n devopsdozo
kubectl get ingress -n devopsdozo

kubectl logs -n devopsdozo -l app=backend

kubectl logs -n devopsdozo -l app=frontend

# access the app locally
# port forward backend
kubectl port-forward -n devopsdozo svc/backend 8000:8000

curl http://localhost:8000/api/topics

## to check the db connection for troubleshooting
kubectl run debug-pod  -n devopsdozo --rm -it --image=postgres -- bash
PGPASSWORD=postgrespassword psql -h devopsdozo-db.devopsdozo.svc.cluster.local -U postgres -d devopsdozo
# run query
SELECT COUNT(*) FROM topics;


# port forward the frontend 
kubectl port-forward svc/frontend 8080:80 -n devopsdozo

```

## Step 8: Access the Application via engress

After deployment, find the ALB URL:

```bash

kubectl apply -f k8s/ingress.yaml

kubectl get ingress -n devopsdozo

# After ingress creation
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# NOte: make sure public subnet are available. and they have Key=kubernetes.io/role/elb,Value=1 tag
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-06a34931ca660b90b" --query "Subnets[*].{SubnetId:SubnetId,AvailabilityZone:AvailabilityZone,PublicIp:MapPublicIpOnLaunch,Tags:Tags}" --output table

# For public subnets (used by internet-facing load balancers)
aws ec2 create-tags --resources subnet-0d0a4f444ffb997ad subnet-046bd3dcc8c11e02d subnet-0d6b5043f6ef0c1c2 subnet-017990e7212e04fb8   --tags Key=kubernetes.io/role/elb,Value=1

# For private subnets (used by internal load balancers) - if needed later
# aws ec2 create-tags --resources subnet-id3 subnet-id4 --tags Key=kubernetes.io/role/internal-elb,Value=1

# verify tags
aws ec2 describe-subnets --subnet-ids subnet-id1 subnet-id2 --query "Subnets[*].{SubnetId:SubnetId,Tags:Tags}" --output table

# delete and recreate ingress
kubectl delete ingress devopsdozo-ingress -n devopsdozo
kubectl apply -f k8s/ingress.yaml

# check the status again
kubectl describe ingress devopsdozo-ingress -n devopsdozo


# Monitor the AWS Load Balancer Controller logs to see if it's processing your Ingress:
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# check if the ALB created -> in ec2 dashboard
```

This will give you the external address of the ALB. Use this address to access your application.

## Step 9: Set up DNS (Optional)

If you have a domain name, you can create a CNAME record pointing to the ALB address:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id <your-hosted-zone-id> \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "devops-learning.yourdomain.com",
          "Type": "CNAME",
          "TTL": 300,
          "ResourceRecords": [
            {
              "Value": "<your-alb-address>"
            }
          ]
        }
      }
    ]
  }'
```

Replace `<your-hosted-zone-id>` and `<your-alb-address>` with your actual values.

## Troubleshooting

### Check Pod Logs
```bash
kubectl logs -f deploy/backend -n devopsdozo
kubectl logs -f deploy/frontend -n devopsdozo
```

### Check Pod Status
```bash
kubectl describe pod -l app=backend -n devopsdozo
kubectl describe pod -l app=frontend -n devopsdozo
```

### Restart Deployments
```bash
kubectl rollout restart deployment backend -n devopsdozo
kubectl rollout restart deployment frontend -n devopsdozo
```


########### Monitoring  #######

##Set Up Monitoring and Logging

Run the setup-monitoring.sh script:

```bash
chmod +x setup-monitoring.sh
./setup-monitoring.sh

# Troubleshooting if prom/grafana pods dont come up
# -> check if the storage is provisioned -> check pvc, descrobe and see the events 
# issue might be with csi driver for storage 

kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver

# EBS CSI driver in your EKS cluster
######### or use EKSCTL #############################################################

# Create IAM policy
# https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/example-iam-policy.json
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-ebs-csi-driver/master/docs/example-iam-policy.json
aws iam create-policy \
  --policy-name AmazonEKS_EBS_CSI_Driver_Policy \
  --policy-document file://example-iam-policy.json

# Create service account with role
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster $cluster_name \
  --attach-policy-arn arn:aws:iam::879381241087:policy/AmazonEKS_EBS_CSI_Driver_Policy \
  --approve \
  --role-name AmazonEKS_EBS_CSI_Driver_Role

## Install the EBS CSI driver using the AWS EKS add-on:

eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster $cluster_name \
  --service-account-role-arn arn:aws:iam::879381241087:role/AmazonEKS_EBS_CSI_Driver_Role \
  --force

# verify installation
# check existing add ons
eksctl get addon --cluster $cluster_name
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
######### ### #############################################################

######### or use helm #############################################################
# If not installing with eksctl
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update
helm upgrade --install aws-ebs-csi-driver \
  --namespace kube-system \
  aws-ebs-csi-driver/aws-ebs-csi-driver

# verify installation
# check existing add ons
eksctl get addon --cluster $cluster_name
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
######### ### #############################################################

# Now reinstall grafana and promethus
helm uninstall prometheus -n monitoring
helm uninstall grafana -n monitoring

./setup-monitoring.sh


# Install AWS CloudWatch Logs agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-serviceaccount.yaml
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-configmap.yaml
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cwagent/cwagent-daemonset.yaml


# Quick access 
# For Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:80

# For Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

```

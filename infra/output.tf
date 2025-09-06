# EKS Cluster Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_arn" {
  description = "The Amazon Resource Name (ARN) of the cluster"
  value       = module.eks.cluster_arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = module.eks.cluster_oidc_issuer_url
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.eks_network.vpc_id
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.eks_network.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.eks_network.public_subnets
}

# EBS CSI Driver IRSA Role
output "ebs_csi_irsa_role_arn" {
  description = "ARN of the IAM role for EBS CSI Driver"
  value       = module.ebs_csi_irsa_role.iam_role_arn
}

# Database Outputs
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "db_instance_name" {
  description = "RDS instance name"
  value       = aws_db_instance.postgres.identifier
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_link.arn
}

# Kubectl Configuration Command
output "configure_kubectl" {
  description = "Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# Commented out until OIDC module is enabled
# output "github_actions_role_arn" {
#   description = "ARN of the IAM role for GitHub Actions"
#   value       = module.oidc.role_arn
# }
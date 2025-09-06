module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"  # Using v20 to maintain aws-auth compatibility

  cluster_name    = "${var.prefix}-${var.environment}-cluster"
  cluster_version = "1.31"  # Latest stable version with good support

  bootstrap_self_managed_addons = false
  
  # EKS Addons with proper configuration
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    eks-pod-identity-agent = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
      before_compute = true  # Ensure CNI is ready before nodes join
    }
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn
    }
  }

  # Optional
  cluster_endpoint_public_access = true

  # Optional: Adds the current caller identity as an administrator via cluster access entry
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.eks_network.vpc_id
  subnet_ids = module.eks_network.private_subnets

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    instance_types = ["t3.medium", "t3.micro"]
    
    # Ensure proper IAM permissions for EBS volumes (backup to IRSA)
    iam_role_additional_policies = {
      AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
    }
  }

  eks_managed_node_groups = {
    example = {
      # Starting on 1.30, AL2023 is the default AMI type for EKS managed node groups
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = ["t3.medium"]

      min_size     = 1
      max_size     = 3
      desired_size = 2
      
      # Ensure nodes wait for addons to be ready
      depends_on = [
        module.eks.cluster_addons
      ]
    }
  }

  tags = {
    Environment = var.environment
    Terraform   = "true"
    repo        = "DevOpsDojo"
  }
}

# # IRSA role for EBS CSI Driver
# module "ebs_csi_irsa_role" {
#   source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

#   role_name             = "${var.prefix}-${var.environment}-ebs-csi-role"
#   attach_ebs_csi_policy = true

#   oidc_providers = {
#     ex = {
#       provider_arn               = module.eks.oidc_provider_arn
#       namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
#     }
#   }

#   tags = {
#     Environment = var.environment
#     Terraform   = "true"
#     repo        = "DevOpsDojo"
#   }
# }
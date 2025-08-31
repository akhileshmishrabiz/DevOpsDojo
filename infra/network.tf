### Using the local module ###
# module "eks_network" {
#   source               = "./modules/network"
#   aws_azs              = ["ap-south-1a", "ap-south-1b"]
#   private_subnets_cidr = ["10.0.8.0/24", "10.0.9.0/24"]
#   public_subnets_cidr  = ["10.0.3.0/24", "10.0.4.0/24"]
#   vpc_name             = "${var.prefix}-${var.environment}-vpc"
#   vpc_cidr             = "10.0.0.0/16"
# }


## using a public module ##
module "eks_network" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Using v5 for AWS Provider v5 compatibility

  name = "${var.prefix}-${var.environment}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["ap-south-1a", "ap-south-1b"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24", "10.0.4.0/24"]

  enable_nat_gateway = true  #  Use a single NAT Gateway
  single_nat_gateway = true  # Keep costs low by using only one NAT Gateway

  enable_dns_hostnames = true
  enable_dns_support   = true

  # Required tags for EKS cluster subnet discovery
  public_subnet_tags = {
    "kubernetes.io/cluster/${var.prefix}-${var.environment}-cluster" = "shared"
    "kubernetes.io/role/elb"                                         = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.prefix}-${var.environment}-cluster" = "shared"
    "kubernetes.io/role/internal-elb"                                = "1"
  }
}

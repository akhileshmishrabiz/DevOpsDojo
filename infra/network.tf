module "eks_network" {
  source               = "./modules/network"
  aws_azs              = ["ap-south-1a", "ap-south-1b"]
  private_subnets_cidr = ["10.0.8.0/24", "10.0.9.0/24"]
  public_subnets_cidr  = ["10.0.3.0/24", "10.0.4.0/24"]
  vpc_name             = "${var.prefix}-${var.environment}-vpc"
  vpc_cidr             = "10.0.0.0/16"
}
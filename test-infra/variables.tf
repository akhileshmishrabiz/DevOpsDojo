# vpc cidr
variable "vpc_cidr" {
  type        = string
  description = "cidr for vpc"
}

# vpc_name
variable "vpc_name" {
  type        = string
  description = "name for vpc"
}

# public subnet data
variable "public_subnet_data" {
  type = list(object({
    cidr              = string
    availability_zone = string
    prefix            = string
  }))
  description = "List of public subnets to create"
}

# private subnet data
variable "private_subnet_data" {
  type = list(object({
    cidr              = string
    availability_zone = string
    prefix            = string
  }))
  description = "List of private subnets to create"
}

# enable nat gateway
variable "enable_nat_gateway" {
  type        = bool
  description = "Whether to create NAT gateway for private subnets"
  default     = true
}

# single nat gateway
variable "single_nat_gateway" {
  type        = bool
  description = "Whether to use a single NAT gateway for all private subnets or one per AZ"
  default     = false
}

# enable dns hostnames
variable "enable_dns_hostnames" {
  type        = bool
  description = "Enable DNS hostnames in the VPC"
  default     = true
}

# enable dns support
variable "enable_dns_support" {
  type        = bool
  description = "Enable DNS support in the VPC"
  default     = true
}

# common tags
variable "common_tags" {
  type        = map(string)
  description = "Common tags to apply to all resources"
  default     = {}
}

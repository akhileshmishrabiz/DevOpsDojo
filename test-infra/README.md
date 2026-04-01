# AWS VPC Terraform Module

A comprehensive Terraform module for creating AWS VPC infrastructure with support for public/private subnets, NAT gateways, and flexible networking configurations.

## Features

- Creates VPC with customizable CIDR block
- Supports multiple public and private subnets across availability zones
- Internet Gateway for public subnet connectivity
- Optional NAT Gateway for private subnet internet access
- Flexible NAT Gateway deployment (single or multi-AZ)
- Automatic route table configuration
- DNS hostname and DNS support configuration
- Comprehensive resource tagging support
- Outputs for all created resources

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 4.0 |

## Usage

### Basic Example

Create a VPC with public and private subnets across two availability zones:

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "my-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      prefix            = "public"
    },
    {
      cidr              = "10.0.2.0/24"
      availability_zone = "us-east-1b"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "10.0.3.0/24"
      availability_zone = "us-east-1a"
      prefix            = "private"
    },
    {
      cidr              = "10.0.4.0/24"
      availability_zone = "us-east-1b"
      prefix            = "private"
    }
  ]

  enable_nat_gateway = true
  single_nat_gateway = false

  common_tags = {
    Environment = "production"
    Terraform   = "true"
  }
}
```

### Single NAT Gateway Example

Use a single NAT Gateway for cost optimization (all private subnets route through one NAT):

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "dev-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "us-west-2a"
      prefix            = "public"
    },
    {
      cidr              = "10.0.2.0/24"
      availability_zone = "us-west-2b"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "10.0.3.0/24"
      availability_zone = "us-west-2a"
      prefix            = "app"
    },
    {
      cidr              = "10.0.4.0/24"
      availability_zone = "us-west-2b"
      prefix            = "app"
    }
  ]

  enable_nat_gateway = true
  single_nat_gateway = true  # Single NAT for cost savings

  common_tags = {
    Environment = "development"
    Project     = "my-project"
  }
}
```

### Multi-Tier Architecture Example

Create a three-tier architecture with public, application, and database subnets:

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "prod-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      prefix            = "public"
    },
    {
      cidr              = "10.0.2.0/24"
      availability_zone = "us-east-1b"
      prefix            = "public"
    },
    {
      cidr              = "10.0.3.0/24"
      availability_zone = "us-east-1c"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "10.0.11.0/24"
      availability_zone = "us-east-1a"
      prefix            = "app"
    },
    {
      cidr              = "10.0.12.0/24"
      availability_zone = "us-east-1b"
      prefix            = "app"
    },
    {
      cidr              = "10.0.13.0/24"
      availability_zone = "us-east-1c"
      prefix            = "app"
    },
    {
      cidr              = "10.0.21.0/24"
      availability_zone = "us-east-1a"
      prefix            = "db"
    },
    {
      cidr              = "10.0.22.0/24"
      availability_zone = "us-east-1b"
      prefix            = "db"
    },
    {
      cidr              = "10.0.23.0/24"
      availability_zone = "us-east-1c"
      prefix            = "db"
    }
  ]

  enable_nat_gateway = true
  single_nat_gateway = false  # One NAT per AZ for high availability

  enable_dns_hostnames = true
  enable_dns_support   = true

  common_tags = {
    Environment = "production"
    Team        = "platform"
    CostCenter  = "engineering"
  }
}

# Reference outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_app_subnets" {
  value = slice(module.vpc.private_subnet_ids, 0, 3)
}

output "private_db_subnets" {
  value = slice(module.vpc.private_subnet_ids, 3, 6)
}
```

### Public-Only VPC Example

Create a VPC with only public subnets (no NAT Gateway needed):

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "public-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "eu-west-1a"
      prefix            = "public"
    },
    {
      cidr              = "10.0.2.0/24"
      availability_zone = "eu-west-1b"
      prefix            = "public"
    }
  ]

  private_subnet_data = []  # No private subnets

  enable_nat_gateway = false  # No NAT Gateway needed

  common_tags = {
    Environment = "testing"
  }
}
```

### Minimal Example

Simplest possible configuration:

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "simple-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "10.0.2.0/24"
      availability_zone = "us-east-1a"
      prefix            = "private"
    }
  ]
}
```

### High Availability Example

Production-ready setup with multiple AZs and redundant NAT Gateways:

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "172.16.0.0/16"
  vpc_name = "ha-prod-vpc"

  public_subnet_data = [
    {
      cidr              = "172.16.0.0/24"
      availability_zone = "ap-south-1a"
      prefix            = "public"
    },
    {
      cidr              = "172.16.1.0/24"
      availability_zone = "ap-south-1b"
      prefix            = "public"
    },
    {
      cidr              = "172.16.2.0/24"
      availability_zone = "ap-south-1c"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "172.16.10.0/24"
      availability_zone = "ap-south-1a"
      prefix            = "private"
    },
    {
      cidr              = "172.16.11.0/24"
      availability_zone = "ap-south-1b"
      prefix            = "private"
    },
    {
      cidr              = "172.16.12.0/24"
      availability_zone = "ap-south-1c"
      prefix            = "private"
    }
  ]

  enable_nat_gateway = true
  single_nat_gateway = false  # NAT per AZ for HA

  enable_dns_hostnames = true
  enable_dns_support   = true

  common_tags = {
    Environment       = "production"
    Terraform         = "true"
    HighAvailability  = "true"
    BackupSchedule    = "daily"
  }
}
```

### Using Module Outputs

Example of using the module outputs in your main configuration:

```hcl
module "vpc" {
  source = "github.com/yourusername/network-module//test-infra"

  vpc_cidr = "10.0.0.0/16"
  vpc_name = "app-vpc"

  public_subnet_data = [
    {
      cidr              = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      prefix            = "public"
    }
  ]

  private_subnet_data = [
    {
      cidr              = "10.0.10.0/24"
      availability_zone = "us-east-1a"
      prefix            = "app"
    }
  ]
}

# Use VPC outputs to create security groups
resource "aws_security_group" "app" {
  name        = "app-sg"
  description = "Security group for application"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr]
  }

  tags = {
    Name = "app-sg"
  }
}

# Use subnet outputs to launch EC2 instances
resource "aws_instance" "app" {
  ami           = "ami-12345678"
  instance_type = "t3.micro"
  subnet_id     = module.vpc.private_subnet_ids[0]

  tags = {
    Name = "app-server"
  }
}

# Use NAT Gateway IPs for allowlisting
output "nat_ips_for_allowlist" {
  description = "NAT Gateway IPs to allowlist in external services"
  value       = module.vpc.nat_gateway_public_ips
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| vpc_cidr | CIDR block for VPC | `string` | n/a | yes |
| vpc_name | Name tag for VPC | `string` | n/a | yes |
| public_subnet_data | List of public subnets to create | `list(object({cidr=string, availability_zone=string, prefix=string}))` | n/a | yes |
| private_subnet_data | List of private subnets to create | `list(object({cidr=string, availability_zone=string, prefix=string}))` | n/a | yes |
| enable_nat_gateway | Whether to create NAT gateway for private subnets | `bool` | `true` | no |
| single_nat_gateway | Whether to use a single NAT gateway for all private subnets or one per AZ | `bool` | `false` | no |
| enable_dns_hostnames | Enable DNS hostnames in the VPC | `bool` | `true` | no |
| enable_dns_support | Enable DNS support in the VPC | `bool` | `true` | no |
| common_tags | Common tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | The ID of the VPC |
| vpc_cidr | The CIDR block of the VPC |
| vpc_arn | The ARN of the VPC |
| internet_gateway_id | The ID of the Internet Gateway |
| public_subnet_ids | List of IDs of public subnets |
| public_subnet_cidrs | List of CIDR blocks of public subnets |
| public_subnet_arns | List of ARNs of public subnets |
| private_subnet_ids | List of IDs of private subnets |
| private_subnet_cidrs | List of CIDR blocks of private subnets |
| private_subnet_arns | List of ARNs of private subnets |
| nat_gateway_ids | List of NAT Gateway IDs |
| nat_gateway_public_ips | List of public Elastic IPs created for AWS NAT Gateway |
| public_route_table_id | ID of public route table |
| private_route_table_ids | List of IDs of private route tables |

## Architecture Diagrams

### Single NAT Gateway Architecture
```
Internet
    |
Internet Gateway
    |
Public Subnets (us-east-1a, us-east-1b)
    |
NAT Gateway (single, in us-east-1a)
    |
Private Subnets (us-east-1a, us-east-1b)
```

### Multi-AZ NAT Gateway Architecture (High Availability)
```
Internet
    |
Internet Gateway
    |
Public Subnets
    |         |
NAT-GW-1a  NAT-GW-1b
    |         |
Private-1a  Private-1b
```

## Cost Considerations

### NAT Gateway Costs
- **Single NAT Gateway**: ~$32/month + data transfer (~$0.045/GB)
- **Multi-AZ NAT Gateways**: Cost multiplies by number of AZs
- **Development/Testing**: Use `single_nat_gateway = true` to minimize costs
- **Production**: Use `single_nat_gateway = false` for high availability

### Cost Optimization Tips
1. Use single NAT Gateway for non-production environments
2. Consider VPC endpoints for AWS services to avoid NAT data transfer costs
3. Use `enable_nat_gateway = false` if private subnets don't need internet access
4. Monitor data transfer costs through NAT Gateways

## Best Practices

1. **CIDR Planning**: Plan your CIDR blocks carefully to allow for future growth
2. **Availability Zones**: Use at least 2 AZs for production workloads
3. **Subnet Sizing**: Allocate subnet sizes based on expected resource count
4. **NAT Strategy**:
   - Development: Single NAT Gateway
   - Production: Multi-AZ NAT Gateways for high availability
5. **Tagging**: Use consistent tagging strategy with `common_tags`
6. **DNS**: Keep DNS hostnames and support enabled for better service integration
7. **Security**: This module creates network infrastructure only - implement security groups and NACLs separately

## Common Issues

### Issue: Terraform destroy fails with "DependencyViolation"
**Solution**: Ensure all resources using the VPC (EC2, RDS, etc.) are destroyed first

### Issue: NAT Gateway creation timeout
**Solution**: NAT Gateways can take 2-5 minutes to create. Increase timeout if needed

### Issue: Insufficient IP addresses in subnet
**Solution**: Use larger CIDR blocks (/24 provides 251 usable IPs, /23 provides 507)

## Examples Repository

Check the `/examples` directory for more use cases:
- EKS cluster networking
- RDS with private subnets
- Multi-region VPC setup
- VPC peering configuration

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - see LICENSE file for details

## Authors

Created and maintained by [Your Name](https://github.com/yourusername)

## Changelog

### v1.0.0 (2026-04-01)
- Initial release
- VPC with public/private subnets
- NAT Gateway support (single and multi-AZ)
- Internet Gateway
- Route tables and associations
- Comprehensive outputs

## Support

For issues, questions, or contributions, please open an issue on [GitHub](https://github.com/yourusername/network-module/issues).

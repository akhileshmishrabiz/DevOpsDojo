# ─── VPC ──────────────────────────────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(
    {
      Name = var.vpc_name
    },
    var.common_tags
  )
}

# ─── Internet Gateway ─────────────────────────────────────────────────────────

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = "${var.vpc_name}-igw"
    },
    var.common_tags
  )
}

# ─── Public Subnets ───────────────────────────────────────────────────────────

resource "aws_subnet" "public" {
  count = length(var.public_subnet_data)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_data[count.index].cidr
  map_public_ip_on_launch = true
  availability_zone       = var.public_subnet_data[count.index].availability_zone

  tags = merge(
    {
      Name = "${var.vpc_name}-${var.public_subnet_data[count.index].prefix}-${count.index + 1}"
      Type = "public"
    },
    var.common_tags
  )
}

# ─── Private Subnets ──────────────────────────────────────────────────────────

resource "aws_subnet" "private" {
  count = length(var.private_subnet_data)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_data[count.index].cidr
  map_public_ip_on_launch = false
  availability_zone       = var.private_subnet_data[count.index].availability_zone

  tags = merge(
    {
      Name = "${var.vpc_name}-${var.private_subnet_data[count.index].prefix}-${count.index + 1}"
      Type = "private"
    },
    var.common_tags
  )
}

# ─── Elastic IPs for NAT Gateway ──────────────────────────────────────────────

resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_data)) : 0

  domain = "vpc"

  tags = merge(
    {
      Name = var.single_nat_gateway ? "${var.vpc_name}-nat-eip" : "${var.vpc_name}-nat-eip-${count.index + 1}"
    },
    var.common_tags
  )

  depends_on = [aws_internet_gateway.main]
}

# ─── NAT Gateway ──────────────────────────────────────────────────────────────

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_data)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    {
      Name = var.single_nat_gateway ? "${var.vpc_name}-nat-gw" : "${var.vpc_name}-nat-gw-${count.index + 1}"
    },
    var.common_tags
  )

  depends_on = [aws_internet_gateway.main]
}

# ─── Public Route Table ───────────────────────────────────────────────────────

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = "${var.vpc_name}-public-rt"
      Type = "public"
    },
    var.common_tags
  )
}

# ─── Public Route ─────────────────────────────────────────────────────────────

resource "aws_route" "public_internet_gateway" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# ─── Public Route Table Association ───────────────────────────────────────────

resource "aws_route_table_association" "public" {
  count = length(var.public_subnet_data)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ─── Private Route Tables ─────────────────────────────────────────────────────

resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnet_data)) : 1

  vpc_id = aws_vpc.main.id

  tags = merge(
    {
      Name = var.single_nat_gateway ? "${var.vpc_name}-private-rt" : "${var.vpc_name}-private-rt-${count.index + 1}"
      Type = "private"
    },
    var.common_tags
  )
}

# ─── Private Route (NAT Gateway) ──────────────────────────────────────────────

resource "aws_route" "private_nat_gateway" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.private_subnet_data)) : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.main[0].id : aws_nat_gateway.main[count.index].id
}

# ─── Private Route Table Association ──────────────────────────────────────────

resource "aws_route_table_association" "private" {
  count = length(var.private_subnet_data)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = var.single_nat_gateway ? aws_route_table.private[0].id : aws_route_table.private[count.index].id
}

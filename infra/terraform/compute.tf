data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "shelfsense_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_pair_name

  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.shelfsense_server.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size
    encrypted   = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-server"
  }
}

resource "aws_eip" "shelfsense_server" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-server-eip"
  }
}

resource "aws_eip_association" "shelfsense_server" {
  allocation_id = aws_eip.shelfsense_server.id
  instance_id   = aws_instance.shelfsense_server.id

  depends_on = [aws_internet_gateway.main]
}

resource "aws_security_group" "shelfsense_server" {
  name        = "${var.project_name}-${var.environment}-server-sg"
  description = "Controls inbound and outbound traffic for the ShelfSense server"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-server-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.shelfsense_server.id

  description = "Allow SSH access from the administrator IP"
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
  cidr_ipv4   = var.ssh_allowed_cidr
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.shelfsense_server.id

  description = "Allow public HTTP traffic"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "all_outbound" {
  security_group_id = aws_security_group.shelfsense_server.id

  description = "Allow the server to reach external services"
  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"
}

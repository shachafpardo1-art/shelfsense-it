resource "aws_ebs_volume" "postgres_data" {
  availability_zone = var.availability_zone
  size              = var.volume_size
  type              = var.volume_type
  encrypted         = true

  tags = {
    Name      = "${var.project_name}-postgres-data"
    Component = "PostgreSQL"
    DataRole  = "PersistentDatabase"
  }

  lifecycle {
    prevent_destroy = true

    precondition {
      condition     = can(regex("^${var.aws_region}[a-z]$", var.availability_zone))
      error_message = "availability_zone must belong to aws_region; for example, eu-central-1a belongs to eu-central-1."
    }
  }
}

resource "aws_ebs_volume" "jenkins_data" {
  availability_zone = var.availability_zone
  size              = 10
  type              = "gp3"
  encrypted         = true

  tags = {
    Name      = "${var.project_name}-jenkins-data"
    Component = "Jenkins"
    DataRole  = "PersistentCIController"
  }

  lifecycle {
    prevent_destroy = true

    precondition {
      condition     = can(regex("^${var.aws_region}[a-z]$", var.availability_zone))
      error_message = "availability_zone must belong to aws_region; for example, eu-central-1a belongs to eu-central-1."
    }
  }
}

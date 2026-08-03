resource "aws_volume_attachment" "postgres_data" {
  device_name = var.persistent_postgres_attachment_device_name
  volume_id   = var.persistent_postgres_volume_id
  instance_id = aws_instance.shelfsense_server.id

  lifecycle {
    precondition {
      condition = (
        can(regex("^${var.aws_region}[a-z]$", var.persistent_postgres_availability_zone)) &&
        var.availability_zone == var.persistent_postgres_availability_zone
      )
      error_message = "The persistent PostgreSQL Availability Zone must belong to aws_region and exactly match the runtime Availability Zone."
    }
  }
}

resource "aws_volume_attachment" "jenkins_data" {
  device_name = var.persistent_jenkins_attachment_device_name
  volume_id   = var.persistent_jenkins_volume_id
  instance_id = aws_instance.shelfsense_server.id

  lifecycle {
    precondition {
      condition = (
        var.persistent_jenkins_volume_id != var.persistent_postgres_volume_id &&
        var.persistent_jenkins_attachment_device_name != var.persistent_postgres_attachment_device_name
      )
      error_message = "Jenkins and PostgreSQL must use distinct EBS volume IDs and requested attachment device names."
    }
  }
}

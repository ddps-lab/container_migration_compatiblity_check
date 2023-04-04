provider "aws" {
  profile = "default"
  region = "us-west-2"
}

resource "aws_instance" "test" {
  count = length(local.group[var.group_number])
  instance_type = random_shuffle.shuffled.result[count.index]
  ami = "ami-0c7a974f58b92cfc6" # migration compatibility test on x86
  key_name = "junho_us"
  subnet_id = local.existing_subnet == null ? aws_subnet.public_subnet[0].id : data.aws_subnets.existing_subnets.ids[0]
  
  vpc_security_group_ids = [
    local.existing_security_group == null ? aws_security_group.security_group[0].id : data.aws_security_groups.existing_security_groups.ids[0]
  ]

  tags = {
    "Name" = "container-migration-test_${random_shuffle.shuffled.result[count.index]}"
  }

  depends_on = [
    aws_efs_mount_target.mount_target,
  ]

  user_data = <<-EOF
            #!/bin/bash
            mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport ${aws_efs_file_system.efs.dns_name}:/ /home/ec2-user/podman/dump
            sudo chown ec2-user:ec2-user /home/ec2-user/podman/dump
            sudo timedatectl set-timezone 'Asia/Seoul'
            sudo hostnamectl set-hostname ${random_shuffle.shuffled.result[count.index]}
            EOF
}


resource "null_resource" "init_inventory" {
  depends_on = [
    aws_instance.test
  ]

  provisioner "local-exec" {
    command = "rm ../ansible/inventory_${var.group_number}.txt || true"
  }
}

resource "null_resource" "write_inventory" {
  count = length(local.group[var.group_number])
  depends_on = [
    null_resource.init_inventory
  ]

  provisioner "local-exec" {
    command = "echo '${aws_instance.test[count.index].public_ip}' >> ../ansible/inventory_${var.group_number}.txt"
  }
}
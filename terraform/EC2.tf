provider "aws" {
  profile = "default"
  region = "us-west-2"
}

variable "instance_type" {
  default = ["m5a.large", "r5a.large", "r5ad.large"]
}

resource "aws_instance" "test" {
  count = 3
  # instance_type = random_shuffle.shuffled.result[count.index]
  instance_type = var.instance_type[count.index]
  ami = "ami-017db8d2adf836dc3" # migration compatibility test on x86
  key_name = "junho_us"
  subnet_id = aws_subnet.public_subnet.id
  
  vpc_security_group_ids = [
    aws_security_group.security_group.id
  ]

  tags = {
    "Name" = "container-migration-test_${random_shuffle.shuffled.result[count.index]}"
  }

  depends_on = [
    aws_efs_mount_target.mount_target
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
    command = "rm ../ansible/inventory.txt"
  }
}

resource "null_resource" "write_inventory" {
  count = 3
  depends_on = [
    null_resource.init_inventory
  ]

  provisioner "local-exec" {
    command = "echo '${aws_instance.test[count.index].public_ip}' >> ../ansible/inventory.txt"
  }
}
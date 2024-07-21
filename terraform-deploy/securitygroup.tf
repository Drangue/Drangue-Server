# SG for Fargate Task
resource "aws_security_group" "ecs_task_sg" {
  name        = "${var.project_name}-fargate-task-sg"
  description = "Security group for Fargate Task"
  vpc_id      = data.aws_vpc.main.id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
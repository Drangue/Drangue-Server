# Create ECR Repository
resource "aws_ecr_repository" "ecr" {
  name         = "${var.project_name}-repo"
  force_delete = "true"
}

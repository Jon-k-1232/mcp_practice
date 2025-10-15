provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.default_tags,
      {
        "Environment" = var.environment
        "Project"     = var.project_name
      }
    )
  }
}

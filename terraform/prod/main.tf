locals {
  service_name = "${var.project_name}-rally"
  tags = merge(
    var.default_tags,
    {
      "Project"     = var.project_name
      "Environment" = var.environment
    }
  )
}

module "ecr_repository" {
  source = "../../modules/ecr"

  name                    = "${var.project_name}-${var.environment}"
  kms_key_arn             = null
  tags                    = local.tags
  image_tag_mutability    = "IMMUTABLE"
  scan_on_push            = true
  enable_lifecycle_policy = true
}

module "ecs_service" {
  source = "../../modules/ecs_service"

  name                      = local.service_name
  environment               = var.environment
  aws_region                = var.aws_region
  vpc_id                    = var.vpc_id
  public_subnet_ids         = var.public_subnet_ids
  private_subnet_ids        = var.private_subnet_ids
  container_image           = "${module.ecr_repository.repository_url}:${var.container_image_tag}"
  container_port            = var.container_port
  desired_count             = var.desired_count
  task_cpu                  = var.task_cpu
  task_memory               = var.task_memory
  health_check_path         = var.health_check_path
  listener_protocol         = var.listener_protocol
  listener_certificate_arn  = var.listener_certificate_arn
  lb_ingress_cidrs          = var.alb_ingress_cidrs
  assign_public_ip          = var.assign_public_ip
  enable_execute_command    = var.enable_execute_command
  enable_container_insights = var.enable_container_insights
  container_environment     = var.container_environment
  tags                      = local.tags
}

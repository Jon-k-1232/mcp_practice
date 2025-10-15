output "ecr_repository_url" {
  description = "URL of the ECR repository."
  value       = module.ecr_repository.repository_url
}

output "service_alb_dns" {
  description = "Public DNS of the service load balancer."
  value       = module.ecs_service.alb_dns_name
}

output "ecs_cluster_id" {
  description = "ECS Cluster identifier."
  value       = module.ecs_service.cluster_id
}

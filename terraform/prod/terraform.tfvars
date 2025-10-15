project_name        = "mcp-rally"
aws_region          = "us-east-1"
vpc_id              = "vpc-xxxxxxxx"
public_subnet_ids   = ["subnet-public-a", "subnet-public-b"]
private_subnet_ids  = ["subnet-private-a", "subnet-private-b"]
container_image_tag = "release-2024-05-01"
container_port      = 8000
desired_count       = 2
task_cpu            = 1024
task_memory         = 2048
listener_protocol   = "HTTPS"
listener_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
health_check_path   = "/health"
alb_ingress_cidrs   = ["0.0.0.0/0"]
assign_public_ip    = false
enable_execute_command = true
container_environment = [
  {
    name  = "RALLY_API_KEY"
    value = "replace-me"
  },
  {
    name  = "RALLY_BASE_URL"
    value = "https://rally1.rallydev.com"
  }
]
default_tags = {
  "Owner"       = "you@example.com"
  "CostCenter"  = "engineering"
  "Confidentiality" = "internal"
}

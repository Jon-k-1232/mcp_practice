variable "project_name" {
  description = "Name of the project."
  type        = string
}

variable "environment" {
  description = "Environment identifier (e.g. dev)."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy to."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the service runs."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the load balancer."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the ECS tasks."
  type        = list(string)
}

variable "container_image_tag" {
  description = "Container image tag to deploy."
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Application container port."
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Desired ECS task count."
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 1024
}

variable "listener_protocol" {
  description = "Load balancer listener protocol (HTTP or HTTPS)."
  type        = string
  default     = "HTTP"
}

variable "listener_certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener."
  type        = string
  default     = null
}

variable "health_check_path" {
  description = "Health check endpoint path."
  type        = string
  default     = "/health"
}

variable "alb_ingress_cidrs" {
  description = "CIDR blocks permitted to reach the load balancer."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "assign_public_ip" {
  description = "Assign a public IP to ECS tasks."
  type        = bool
  default     = false
}

variable "enable_execute_command" {
  description = "Toggle ECS Exec."
  type        = bool
  default     = true
}

variable "enable_container_insights" {
  description = "Toggle ECS Container Insights."
  type        = bool
  default     = true
}

variable "container_environment" {
  description = "Environment variables passed to the container."
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "default_tags" {
  description = "Default tags applied via provider."
  type        = map(string)
  default     = {}
}

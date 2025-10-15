variable "name" {
  description = "Short name of the service."
  type        = string
}

variable "environment" {
  description = "Environment name (e.g. dev, prod)."
  type        = string
}

variable "aws_region" {
  description = "AWS region where resources are deployed."
  type        = string
}

variable "vpc_id" {
  description = "VPC identifier."
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the load balancer."
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the ECS service."
  type        = list(string)
}

variable "container_image" {
  description = "Full image reference for the container."
  type        = string
}

variable "container_port" {
  description = "Container port exposed by the service."
  type        = number
  default     = 8000
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

variable "cpu_architecture" {
  description = "CPU architecture for the task."
  type        = string
  default     = "X86_64"
}

variable "desired_count" {
  description = "Desired number of ECS tasks."
  type        = number
  default     = 1
}

variable "assign_public_ip" {
  description = "Assign a public IP to each task."
  type        = bool
  default     = false
}

variable "enable_execute_command" {
  description = "Enable ECS Exec for the service."
  type        = bool
  default     = false
}

variable "enable_container_insights" {
  description = "Enable ECS Container Insights."
  type        = bool
  default     = true
}

variable "container_environment" {
  description = "List of environment variables for the container."
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "health_check_path" {
  description = "HTTP health check path for the target group."
  type        = string
  default     = "/health"
}

variable "listener_port" {
  description = "Load balancer listener port."
  type        = number
  default     = 80
}

variable "listener_protocol" {
  description = "Load balancer listener protocol (HTTP or HTTPS)."
  type        = string
  default     = "HTTP"
}

variable "listener_certificate_arn" {
  description = "Certificate ARN for HTTPS listeners."
  type        = string
  default     = null
}

variable "alb_idle_timeout" {
  description = "ALB idle timeout in seconds."
  type        = number
  default     = 60
}

variable "enable_deletion_protection" {
  description = "Enable ALB deletion protection."
  type        = bool
  default     = false
}

variable "lb_ingress_cidrs" {
  description = "CIDR blocks allowed to access the load balancer."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "log_retention_in_days" {
  description = "CloudWatch Logs retention period."
  type        = number
  default     = 30
}

variable "additional_execution_role_policy_arns" {
  description = "Additional IAM policy ARNs to attach to the ECS execution role."
  type        = list(string)
  default     = []
}

variable "task_role_policy_arns" {
  description = "IAM policy ARNs to attach to the ECS task role."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Common tags applied to resources."
  type        = map(string)
  default     = {}
}

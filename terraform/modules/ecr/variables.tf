variable "name" {
  description = "Name of the ECR repository."
  type        = string
}

variable "image_tag_mutability" {
  description = "Whether image tags can be overwritten."
  type        = string
  default     = "IMMUTABLE"
}

variable "scan_on_push" {
  description = "Enable image vulnerability scanning on push."
  type        = bool
  default     = true
}

variable "enable_lifecycle_policy" {
  description = "Whether to create a lifecycle policy for untagged images."
  type        = bool
  default     = true
}

variable "untagged_retention_days" {
  description = "Number of days to retain untagged images."
  type        = number
  default     = 14
}

variable "kms_key_arn" {
  description = "KMS key ARN used for repository encryption. Leave empty to use AWS managed key."
  type        = string
  default     = null
}

variable "tags" {
  description = "Common tags applied to resources."
  type        = map(string)
  default     = {}
}

variable "region" {
  default = "us-east-1"
}

variable "lambda_role_arn" {
  description = "ARN of the shared Lambda execution role"
}

variable "api_gateway_id" {
  description = "ID of the shared API Gateway"
}

variable "api_gateway_execution_arn" {
  description = "Execution ARN of the shared API Gateway"
}

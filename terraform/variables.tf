variable "region" {
  default = "us-east-1"
}


variable "jwt_secret" {
  description = "Secret key for JWT"
  type        = string
  sensitive   = true
}

variable "card_queue_url" {
  description = "URL of the Card Service SQS queue"
  type        = string
}

variable "notification_queue_url" {
  description = "URL of the Notification Service SQS queue"
  type        = string
}

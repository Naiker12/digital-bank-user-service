locals {
  common_tags = {
    Project     = "Digital Bank"
    Service     = "User-Service"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}

resource "aws_dynamodb_table" "user_table" {
  name         = "bank-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uuid"
  range_key    = "document"

  attribute {
    name = "uuid"
    type = "S"
  }
  attribute {
    name = "document"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    projection_type = "ALL"
    hash_key        = "email"
  }

  tags = local.common_tags
}


resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "user_avatars" {
  bucket        = "bank-user-avatars-${random_id.bucket_suffix.hex}"
  force_destroy = true
  tags          = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "user_avatars_public_access" {
  bucket = aws_s3_bucket.user_avatars.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "allow_public_read" {
  bucket = aws_s3_bucket.user_avatars.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.user_avatars.arn}/*"
      }
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.user_avatars_public_access]
}


resource "aws_apigatewayv2_api" "user_api" {
  name          = "bank-user-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
  }
  tags = local.common_tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.user_api.id
  name        = "$default"
  auto_deploy = true
}

# User Service: Register
resource "aws_lambda_function" "register_user" {
  filename         = local.user_zip_path
  function_name    = "register-user-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambdas.register_user.handler"
  runtime          = "python3.13"
  source_code_hash = local.user_zip_hash
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      USERS_TABLE            = aws_dynamodb_table.user_table.name
      CARD_QUEUE_URL         = var.card_queue_url
      NOTIFICATION_QUEUE_URL = var.notification_queue_url
      DEPLOY_TIMESTAMP       = "20260420_1059"
    }
  }
  tags = local.common_tags
}

# User Service: Login
resource "aws_lambda_function" "login_user" {
  filename         = local.user_zip_path
  function_name    = "login-user-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambdas.login_user.handler"
  runtime          = "python3.13"
  source_code_hash = local.user_zip_hash
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      USERS_TABLE            = aws_dynamodb_table.user_table.name
      JWT_SECRET             = var.jwt_secret
      NOTIFICATION_QUEUE_URL = var.notification_queue_url
    }
  }
  tags = local.common_tags
}

# User Service: Get Profile
resource "aws_lambda_function" "get_profile" {
  filename         = local.user_zip_path
  function_name    = "get-profile-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambdas.get_profile.handler"
  runtime          = "python3.13"
  source_code_hash = local.user_zip_hash

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      JWT_SECRET  = var.jwt_secret
    }
  }
  tags = local.common_tags
}

# User Service: Update User
resource "aws_lambda_function" "update_user" {
  filename         = local.user_zip_path
  function_name    = "update-user-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambdas.update_user.handler"
  runtime          = "python3.13"
  source_code_hash = local.user_zip_hash

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      JWT_SECRET  = var.jwt_secret
    }
  }
  tags = local.common_tags
}

# User Service: Upload Avatar
resource "aws_lambda_function" "upload_avatar" {
  filename         = local.user_zip_path
  function_name    = "upload-avatar-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambdas.upload_avatar.handler"
  runtime          = "python3.13"
  source_code_hash = local.user_zip_hash

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      S3_BUCKET   = aws_s3_bucket.user_avatars.id
      JWT_SECRET  = var.jwt_secret
    }
  }
  tags = local.common_tags
}


resource "aws_apigatewayv2_integration" "register" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.register_user.invoke_arn
}

resource "aws_apigatewayv2_route" "register_route" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "POST /users/register"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_integration" "login" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.login_user.invoke_arn
}

resource "aws_apigatewayv2_route" "login_route" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "POST /users/login"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_integration" "get_profile" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_profile.invoke_arn
}

resource "aws_apigatewayv2_route" "get_profile_route" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "GET /users/profile/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.get_profile.id}"
}

resource "aws_apigatewayv2_integration" "update_profile" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.update_user.invoke_arn
}

resource "aws_apigatewayv2_route" "update_profile_route" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "PUT /users/profile/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.update_profile.id}"
}

resource "aws_apigatewayv2_integration" "upload_avatar" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.upload_avatar.invoke_arn
}

resource "aws_apigatewayv2_route" "upload_avatar_route" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "POST /users/profile/{user_id}/avatar"
  target    = "integrations/${aws_apigatewayv2_integration.upload_avatar.id}"
}


resource "aws_lambda_permission" "api_gw_register" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.register_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_login" {
  statement_id  = "AllowExecutionFromAPIGatewayLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_profile" {
  statement_id  = "AllowExecutionFromAPIGatewayProfile"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_profile.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_update" {
  statement_id  = "AllowExecutionFromAPIGatewayUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_avatar" {
  statement_id  = "AllowExecutionFromAPIGatewayAvatar"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_avatar.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}

# --- IAM Roles and Policies ---

resource "aws_iam_role" "lambda_role" {
  name = "bank-user-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_access" {
  name        = "bank-user-service-access-policy"
  description = "Permisos para DynamoDB, SQS y S3 para el servicio de usuarios"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "sqs:*",
          "s3:*",
          "ses:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_access.arn
}

# --- Outputs ---

output "user_table_name" {
  value = aws_dynamodb_table.user_table.name
}

output "user_avatars_bucket" {
  value = aws_s3_bucket.user_avatars.id
}

output "api_base_url" {
  value       = aws_apigatewayv2_api.user_api.api_endpoint
  description = "Base URL of the User Service API Gateway"
}

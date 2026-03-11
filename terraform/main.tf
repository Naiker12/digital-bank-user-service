provider "aws" {
  region = var.region
}

# 1. DynamoDB Tables
resource "aws_dynamodb_table" "user_table" {
  name           = "bank-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "uuid"
  range_key      = "document"

  attribute {
    name = "uuid"
    type = "S"
  }
  attribute {
    name = "document"
    type = "S"
  }
}

# 2. S3 Buckets
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "user_avatars" {
  bucket = "bank-user-avatars-${random_id.bucket_suffix.hex}"
}

# 3. Lambda Functions (Automated Deployment)
data "archive_file" "user_service_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../deployment_package"
  output_path = "${path.module}/user_service.zip"
}

# User Service: Register
resource "aws_lambda_function" "register_user" {
  filename         = data.archive_file.user_service_zip.output_path
  function_name    = "register-user-lambda"
  role             = var.lambda_role_arn
  handler          = "register_user.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.user_service_zip.output_base64sha256

  environment {
    variables = {
      USERS_TABLE            = aws_dynamodb_table.user_table.name
      # URLs are hardcoded as in the original for now (to avoid dependency loops)
      CARD_QUEUE_URL         = "create-request-card-sqs"
      NOTIFICATION_QUEUE_URL = "notification-email-sqs"
      DEPLOY_TIMESTAMP       = "20260309_2210"
    }
  }
}

# User Service: Login
resource "aws_lambda_function" "login_user" {
  filename         = data.archive_file.user_service_zip.output_path
  function_name    = "login-user-lambda"
  role             = var.lambda_role_arn
  handler          = "login_user.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.user_service_zip.output_base64sha256

  environment {
    variables = {
      USERS_TABLE            = aws_dynamodb_table.user_table.name
      JWT_SECRET             = "super-secret-bank-key-2026"
      NOTIFICATION_QUEUE_URL = "notification-email-sqs"
    }
  }
}

# User Service: Get Profile
resource "aws_lambda_function" "get_profile" {
  filename         = data.archive_file.user_service_zip.output_path
  function_name    = "get-profile-lambda"
  role             = var.lambda_role_arn
  handler          = "get_profile.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.user_service_zip.output_base64sha256

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      JWT_SECRET  = "super-secret-bank-key-2026"
    }
  }
}

# User Service: Update User
resource "aws_lambda_function" "update_user" {
  filename         = data.archive_file.user_service_zip.output_path
  function_name    = "update-user-lambda"
  role             = var.lambda_role_arn
  handler          = "update_user.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.user_service_zip.output_base64sha256

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      JWT_SECRET  = "super-secret-bank-key-2026"
    }
  }
}

# User Service: Upload Avatar
resource "aws_lambda_function" "upload_avatar" {
  filename         = data.archive_file.user_service_zip.output_path
  function_name    = "upload-avatar-lambda"
  role             = var.lambda_role_arn
  handler          = "upload_avatar.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.user_service_zip.output_base64sha256

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.user_table.name
      S3_BUCKET   = aws_s3_bucket.user_avatars.id
      JWT_SECRET  = "super-secret-bank-key-2026"
    }
  }
}

# 4. API Integrations
resource "aws_apigatewayv2_integration" "register" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.register_user.invoke_arn
}

resource "aws_apigatewayv2_route" "register_route" {
  api_id    = var.api_gateway_id
  route_key = "POST /register"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_integration" "login" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.login_user.invoke_arn
}

resource "aws_apigatewayv2_route" "login_route" {
  api_id    = var.api_gateway_id
  route_key = "POST /login"
  target    = "integrations/${aws_apigatewayv2_integration.login.id}"
}

resource "aws_apigatewayv2_integration" "get_profile" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_profile.invoke_arn
}

resource "aws_apigatewayv2_route" "get_profile_route" {
  api_id    = var.api_gateway_id
  route_key = "GET /profile/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.get_profile.id}"
}

resource "aws_apigatewayv2_integration" "update_profile" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.update_user.invoke_arn
}

resource "aws_apigatewayv2_route" "update_profile_route" {
  api_id    = var.api_gateway_id
  route_key = "PUT /profile/{user_id}"
  target    = "integrations/${aws_apigatewayv2_integration.update_profile.id}"
}

resource "aws_apigatewayv2_integration" "upload_avatar" {
  api_id           = var.api_gateway_id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.upload_avatar.invoke_arn
}

resource "aws_apigatewayv2_route" "upload_avatar_route" {
  api_id    = var.api_gateway_id
  route_key = "POST /profile/{user_id}/avatar"
  target    = "integrations/${aws_apigatewayv2_integration.upload_avatar.id}"
}

# 5. Permissions
resource "aws_lambda_permission" "api_gw_register" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.register_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_login" {
  statement_id  = "AllowExecutionFromAPIGatewayLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_profile" {
  statement_id  = "AllowExecutionFromAPIGatewayProfile"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_profile.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_update" {
  statement_id  = "AllowExecutionFromAPIGatewayUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.update_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_avatar" {
  statement_id  = "AllowExecutionFromAPIGatewayAvatar"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_avatar.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

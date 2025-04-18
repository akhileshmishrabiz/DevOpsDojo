# main.tf
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "stage" {
  description = "Deployment stage (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# DynamoDB Table for Quiz Results
resource "aws_dynamodb_table" "quiz_results" {
  name         = "QuizResults-${var.stage}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "quizId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "quizId"
    type = "S"
  }

  tags = {
    Project = "DevOpsLearningPlatform"
    Stage   = var.stage
  }
}

# IAM Role for Lambda Function
resource "aws_iam_role" "lambda_role" {
  name = "quiz_analysis_lambda_role_${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = "DevOpsLearningPlatform"
    Stage   = var.stage
  }
}

# Lambda Execution Policy
resource "aws_iam_policy" "lambda_policy" {
  name        = "quiz_analysis_lambda_policy_${var.stage}"
  description = "Policy for quiz analysis Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.quiz_results.arn
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Lambda Function
resource "aws_lambda_function" "quiz_analysis" {
  function_name = "quiz-analysis-${var.stage}"
  filename      = "lambda_function.zip"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.9"
  timeout       = 15
  memory_size   = 256

  environment {
    variables = {
      STAGE          = var.stage
      DYNAMODB_TABLE = aws_dynamodb_table.quiz_results.name
    }
  }

  tags = {
    Project = "DevOpsLearningPlatform"
    Stage   = var.stage
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "quiz_analysis_api" {
  name        = "quiz-analysis-api-${var.stage}"
  description = "API for DevOps Learning Platform quiz analysis"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Project = "DevOpsLearningPlatform"
    Stage   = var.stage
  }
}

# API Gateway Resources
resource "aws_api_gateway_resource" "analyze_results" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  parent_id   = aws_api_gateway_rest_api.quiz_analysis_api.root_resource_id
  path_part   = "analyze-results"
}

resource "aws_api_gateway_resource" "recommendations" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  parent_id   = aws_api_gateway_rest_api.quiz_analysis_api.root_resource_id
  path_part   = "get-recommendations"
}

resource "aws_api_gateway_resource" "track_progress" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  parent_id   = aws_api_gateway_rest_api.quiz_analysis_api.root_resource_id
  path_part   = "track-progress"
}

# API Gateway Methods
resource "aws_api_gateway_method" "analyze_results_post" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.analyze_results.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "recommendations_post" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.recommendations.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "track_progress_post" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.track_progress.id
  http_method   = "POST"
  authorization_type = "NONE"
}

# CORS Configuration
resource "aws_api_gateway_method" "analyze_results_options" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.analyze_results.id
  http_method   = "OPTIONS"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "recommendations_options" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.recommendations.id
  http_method   = "OPTIONS"
  authorization_type = "NONE"
}

resource "aws_api_gateway_method" "track_progress_options" {
  rest_api_id   = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id   = aws_api_gateway_resource.track_progress.id
  http_method   = "OPTIONS"
  authorization_type = "NONE"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "analyze_results_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.analyze_results.id
  http_method             = aws_api_gateway_method.analyze_results_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.quiz_analysis.invoke_arn
}

resource "aws_api_gateway_integration" "recommendations_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.recommendations.id
  http_method             = aws_api_gateway_method.recommendations_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.quiz_analysis.invoke_arn
}

resource "aws_api_gateway_integration" "track_progress_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.track_progress.id
  http_method             = aws_api_gateway_method.track_progress_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.quiz_analysis.invoke_arn
}

# CORS Integrations
resource "aws_api_gateway_integration" "analyze_results_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.analyze_results.id
  http_method             = aws_api_gateway_method.analyze_results_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "recommendations_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.recommendations.id
  http_method             = aws_api_gateway_method.recommendations_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "track_progress_options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id             = aws_api_gateway_resource.track_progress.id
  http_method             = aws_api_gateway_method.track_progress_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# CORS Method Responses
resource "aws_api_gateway_method_response" "analyze_results_options_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.analyze_results.id
  http_method = aws_api_gateway_method.analyze_results_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "recommendations_options_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.recommendations.id
  http_method = aws_api_gateway_method.recommendations_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "track_progress_options_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.track_progress.id
  http_method = aws_api_gateway_method.track_progress_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS Integration Responses
resource "aws_api_gateway_integration_response" "analyze_results_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.analyze_results.id
  http_method = aws_api_gateway_method.analyze_results_options.http_method
  status_code = aws_api_gateway_method_response.analyze_results_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "recommendations_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.recommendations.id
  http_method = aws_api_gateway_method.recommendations_options.http_method
  status_code = aws_api_gateway_method_response.recommendations_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "track_progress_options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  resource_id = aws_api_gateway_resource.track_progress.id
  http_method = aws_api_gateway_method.track_progress_options.http_method
  status_code = aws_api_gateway_method_response.track_progress_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.quiz_analysis.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.quiz_analysis_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "quiz_analysis_deployment" {
  depends_on = [
    aws_api_gateway_integration.analyze_results_integration,
    aws_api_gateway_integration.recommendations_integration,
    aws_api_gateway_integration.track_progress_integration,
    aws_api_gateway_integration.analyze_results_options_integration,
    aws_api_gateway_integration.recommendations_options_integration,
    aws_api_gateway_integration.track_progress_options_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.quiz_analysis_api.id
  stage_name  = var.stage

  lifecycle {
    create_before_destroy = true
  }
}

# Outputs
output "api_gateway_url" {
  description = "API Gateway URL"
  value       = "${aws_api_gateway_deployment.quiz_analysis_deployment.invoke_url}"
}

output "analyze_results_url" {
  description = "URL for analyze-results endpoint"
  value       = "${aws_api_gateway_deployment.quiz_analysis_deployment.invoke_url}/analyze-results"
}

output "recommendations_url" {
  description = "URL for get-recommendations endpoint"
  value       = "${aws_api_gateway_deployment.quiz_analysis_deployment.invoke_url}/get-recommendations"
}

output "track_progress_url" {
  description = "URL for track-progress endpoint"
  value       = "${aws_api_gateway_deployment.quiz_analysis_deployment.invoke_url}/track-progress"
}
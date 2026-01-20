resource "aws_lambda_function" "underground_container" {
  function_name = "commuter-dashboard-underground"
  role          = aws_iam_role.lambda_execution.arn

  package_type = "Image"
  image_uri = "864981741904.dkr.ecr.us-east-1.amazonaws.com/commuter-dashboard-underground:v8"
  publish = true

  timeout      = 30
  memory_size = 512

  environment {
    variables = {
      MTA_API_KEY = var.mta_api_key
    }
  }
}

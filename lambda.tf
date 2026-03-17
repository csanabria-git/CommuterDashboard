resource "aws_lambda_function" "underground_container" {
  function_name = "commuter-dashboard-underground"
  role          = aws_iam_role.lambda_execution.arn

  package_type = "Image"
  image_uri = "864981741904.dkr.ecr.us-east-1.amazonaws.com/commuter-dashboard-underground:1.1.2"
  publish = true

  timeout      = 30
  memory_size = 512

  environment {
    variables = {
      MTA_API_KEY = var.mta_api_key
      MTA_BUSTIME_API_KEY  = var.mta_bustime_api_key # bus (new)
    }
  }
}
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.underground_container.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.commuter_api.execution_arn}/*/*"
}

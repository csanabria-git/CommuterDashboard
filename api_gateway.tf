resource "aws_apigatewayv2_api" "commuter_api" {
  name          = "commuter-dashboard-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.commuter_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.underground_container.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "arrivals" {
  api_id    = aws_apigatewayv2_api.commuter_api.id
  route_key = "GET /arrivals"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.commuter_api.id
  name        = "$default"
  auto_deploy = true
}


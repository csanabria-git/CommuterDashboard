resource "aws_apigatewayv2_domain_name" "commute" {
  domain_name = "commute.csanabria-awslab.com"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.commute.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "commute" {
  api_id      = aws_apigatewayv2_api.commuter_api.id
  domain_name = aws_apigatewayv2_domain_name.commute.domain_name
  stage       = aws_apigatewayv2_stage.default.name
}


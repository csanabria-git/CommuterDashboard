data "aws_route53_zone" "primary" {
  name = "csanabria-awslab.com"
}

resource "aws_route53_record" "commute" {
  zone_id = data.aws_route53_zone.primary.zone_id
  name    = "commute.csanabria-awslab.com"
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.commute.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.commute.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}


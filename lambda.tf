data "archive_file" "commuter_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/commuter_stub"
  output_path = "${path.module}/lambda/commuter_stub.zip"
}

resource "aws_lambda_function" "commuter_stub" {
  function_name = "commuter-dashboard-stub"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.commuter_lambda_zip.output_path
  source_code_hash = data.archive_file.commuter_lambda_zip.output_base64sha256

  timeout      = 10
  memory_size = 128
}


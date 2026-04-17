data "archive_file" "user_service_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../deployment_package"
  output_path = "${path.module}/user_service.zip"
}

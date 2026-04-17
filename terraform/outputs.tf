output "user_table_name" {
  value = aws_dynamodb_table.user_table.name
}

output "user_avatars_bucket" {
  value = aws_s3_bucket.user_avatars.id
}

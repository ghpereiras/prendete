output "iam_user_name" {
  value       = aws_iam_user.prendete_bedrock.name
  description = "Create its access key in the IAM console and set it in Render as AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY."
}

output "allowed_resources" {
  value       = local.model_arns
  description = "The only resources the user can invoke."
}

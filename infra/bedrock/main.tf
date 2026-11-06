terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

locals {
  # A cross-region inference profile fans each request out to the model in several regions, so the policy has
  # to allow the foundation model in any region (the region-less ARN is what a global profile resolves to) and,
  # when one is used, the profile itself. The profile ARN carries the region the call is made from, and a
  # region pinned here made the first real call fail with AccessDenied, so it is a wildcard.
  model_arns = concat(
    [
      "arn:aws:bedrock:*::foundation-model/${var.foundation_model_id}",
      "arn:aws:bedrock:::foundation-model/${var.foundation_model_id}",
    ],
    var.inference_profile_id == "" ? [] : [
      "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/${var.inference_profile_id}"
    ],
  )
}

# The identity Render uses. Its access key is created by hand in the console on purpose: a key created here
# would have its secret written into the Terraform state file.
resource "aws_iam_user" "prendete_bedrock" {
  name = "prendete-bedrock"
}

data "aws_iam_policy_document" "invoke_one_model" {
  statement {
    sid       = "InvokeOneModel"
    actions   = ["bedrock:InvokeModel"] # the Converse API is authorised through this action
    resources = local.model_arns
  }
}

resource "aws_iam_user_policy" "invoke_one_model" {
  name   = "invoke-one-model"
  user   = aws_iam_user.prendete_bedrock.name
  policy = data.aws_iam_policy_document.invoke_one_model.json
}

resource "aws_budgets_budget" "monthly" {
  name         = "prendete-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
}

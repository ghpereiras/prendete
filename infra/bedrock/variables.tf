variable "region" {
  type        = string
  default     = "us-east-1"
  description = "Region the app calls Bedrock in (the backend's AWS_REGION)."
}

variable "foundation_model_id" {
  type        = string
  description = "Foundation model id, without any inference-profile prefix, e.g. anthropic.claude-haiku-4-5-20251001-v1:0. Confirm it in the Bedrock console."
}

variable "inference_profile_id" {
  type        = string
  default     = ""
  description = "Cross-region inference profile id the backend uses as BEDROCK_MODEL_ID (it starts with us. or global.), e.g. global.anthropic.claude-haiku-4-5-20251001-v1:0. Leave empty if the plain model id is called directly."
}

variable "budget_email" {
  type        = string
  description = "Where the budget alert is emailed."
}

variable "monthly_budget_usd" {
  type        = number
  default     = 5
  description = "Monthly budget for the whole account. It only sends an alert; the real spending ceiling is AI_DAILY_LIMIT_* in the backend."
}

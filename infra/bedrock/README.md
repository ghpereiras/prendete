# Bedrock access for the AI feature

Creates what "Create with AI" needs on AWS, with the least privilege that works:

- an IAM user that can do one thing, `bedrock:InvokeModel` on one model (and its inference profile);
- a monthly budget of US$5 that emails you at 80%. It only alerts: the backend's `AI_DAILY_LIMIT_PER_USER` and `AI_DAILY_LIMIT_GLOBAL` are what actually cap spending.

```bash
cd infra/bedrock
terraform init
terraform plan  -var 'foundation_model_id=anthropic.claude-haiku-4-5-20251001-v1:0' \
                -var 'inference_profile_id=global.anthropic.claude-haiku-4-5-20251001-v1:0' \
                -var 'budget_email=you@example.com'
terraform apply   # same -var flags
```

The model ids above are the ones this project was tested with (a `global.` profile works from any region; a `us.` one is the alternative). Copy the exact ids from the Bedrock console, since they change between releases, and request access to the model there first. The policy matches the profile in any region on purpose: its ARN includes the region the call is made from, and pinning one fails with `AccessDenied` as soon as `AWS_REGION` differs.

Then, in the IAM console, create an access key for `prendete-bedrock` and paste it into Render (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) together with `BEDROCK_MODEL_ID` (the inference profile id if you use one) and `AWS_REGION`. The key is not created here because Terraform would write its secret into the state file. Never commit a key: this repository is public.

This was written without being able to run `terraform validate` in the environment it was authored in, so run `terraform plan` and read it before applying.

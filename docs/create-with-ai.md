# Create with AI: design notes

How the "Create with AI" feature works, why the work is split between a language model and plain code the way it is, and what building it taught. For setup and costs see [DEPLOY.md](../DEPLOY.md#ai-feature-aws-bedrock); for the quick overview see the [README](../README.md#create-with-ai).

## What it does

The user types a plan the way they would in a chat: *"cena el viernes a las 21 o el sábado a las 20"*. The app opens the right form already filled in: several dates open the date-poll form, one date opens the event form. The user reviews it and saves, or edits it. Nothing is saved by the AI.

## The request, step by step

1. `frontend/src/pages/CreateWithAi.tsx` sends `POST /ai/plan-draft` with the text and the browser's time zone.
2. `app/routers/ai.py` checks that the feature is on (`BEDROCK_MODEL_ID` set), then the per-user and global limits, counted from the `ai_requests` table over the last 24 hours. This happens **before** any model call, because the limits are the spending ceiling.
3. `app/plan_draft.py` builds the system prompt: the rules, the current date and time, and a 21-day calendar with every weekday already resolved (each day is tagged `[esta semana]` or `[la semana que viene]`).
4. `app/llm.py` calls AWS Bedrock (Converse API) with `temperature` 0, **forcing a single tool** (`draft_plan`). The answer is a JSON object that follows a schema, not text to parse. Timeouts are short and retries limited, because a hung request holds one of the few workers of a free instance.
5. `build_draft` in `app/plan_draft.py` validates and normalises that object. All the rules with a right answer live here (see below).
6. The router logs the call in `ai_requests` (tokens, latency, success; **never the text**) and returns the draft. Failed calls are logged too and count against the limit, so a retry loop cannot run up the bill.
7. The form shows a notice: it is a draft, why it became an event or a poll, and a warning for anything uncertain (for instance "I estimated the time").

## How it decides between model and code

The rule of thumb: **the model reads, the code decides.**

- If the task is *understanding informal language* (what is the title, which days did they mention, did they say the part of the day), it goes to the model.
- If there is *one right answer that can be written as a rule and tested*, it goes to code.
- If the model keeps getting a rule wrong, don't argue with it in the prompt: change its job to **reporting a fact** and let the code apply the rule.

| Decision | Who | How |
| --- | --- | --- |
| Title, description, location | Model | Extracted as written; omitted if absent (never invented) |
| Which days and times the user named | Model | A list of dates, plus recurring days as `weekly` |
| Event or poll | Code | Two or more dates is a poll, otherwise an event |
| A bare hour from 1 to 11 ("a las 9") | Both | The model reports `period_stated` (did the user say morning/evening?); the code adds 12 hours when not, unless the text names a morning plan (desayuno, brunch) |
| "El sábado que viene" | Both | The model reports `relative_weekday`; the code moves the date to the nearest such weekday after today. Only "de la semana que viene" means next week |
| "Los próximos 5 martes" | Both | The model says weekday + count; the code works the dates out (today excluded, 4 if no number, capped) |
| Time when none was given | Both | The model names the part of the day the plan belongs to (`typical_period`: morning, midday, afternoon, late night); the code maps it to 10:00, 13:00, 16:00 or 22:00. No clue means 20:00. Both cases raise a warning |
| Past or duplicate dates, cap of 10 options, sorting | Code | Dropped, deduplicated, truncated, with a warning |
| Time zone and UTC conversion | Code | The browser's zone, Buenos Aires if unknown |
| Duration and capacity | Both | The model extracts them only if stated; the code bounds them, and a poll has no capacity |
| Spending limits, logging, security | Code | Per-user and global daily limits, and nothing reaches the model before they are checked |

Why not put it all in the prompt? Because a rule in a prompt is a request, and the model sometimes ignores it. Code is the same every time and has unit tests.

## Four cases that shaped the design

The eval set (`evals/cases.jsonl`, 48 cases of Argentine Spanish) found real problems:

1. **Bare hours.** The prompt said "a las 10 is evening" and the model returned 10:00 anyway. Fix: it only reports whether the user said the part of the day, and the code adds the 12 hours. The first version of that flag asked the model to judge "the kind of plan" as well and failed again on "previa a las 11"; the flag now judges **only the user's words**, and the morning-plan exception is a keyword rule in code.
2. **"El sábado que viene".** The model returned next week's Saturday twice, even after the prompt said otherwise (its prior for the phrase is stronger than the instruction). Fix: a reported flag, and the code resolves the date.
3. **Recurring days.** The calendar only covers 21 days, so "the next 5 Tuesdays" would have forced the model to do date arithmetic past it, which is exactly what the calendar avoids. Fix: the model says "Tuesday, 5 times" and the code expands it.
4. **Contaminated examples.** Several examples written into the prompt were identical to eval inputs ("Somos 10", "máximo 30", "de 16 a 20"). That inflated the score. They were replaced, and `CLAUDE.md` now forbids it. An eval only measures something while the model has not seen its answers.

## Results

Model: Claude Haiku 4.5 on Bedrock (`global.anthropic.claude-haiku-4-5-20251001-v1:0`).

| Run | Result | What it showed |
| --- | --- | --- |
| First full run (37 cases) | 30 pass; 3 were IAM permission errors, so 30 of the 34 answered | Four real misses: bare hours, "que viene", the start of a time range. It also exposed the contaminated examples |
| Second full run (41 cases) | 39 pass, no errors | Two misses left (a bare "a las 11" and "que viene"); both traced to a rule the model would not follow |
| Final full run (48 cases, 2026-11-06) | **48/48 pass, 0 errors** | Every field at 100%: event or poll, dates (48 cases), capacity (48), title (24), location (7), warnings (11) |

Between the runs, only the cases touched by each change were re-run, and a full run closed the series.

Cost and speed of the final run: 146,194 input and 4,567 output tokens for 48 requests, so about **3,050 input and 95 output tokens per request**, **1.4 s on average**, and an estimated **US$0.17 per full run (about US$0.0035 per request)**. That estimate uses an assumed price of US$1 / US$5 per million tokens and has not been checked against the AWS bill. The prompt grew by about half over the work (roughly 2,050 to 3,050 input tokens) as rules and schema fields were added; caching its fixed part is the obvious saving if cost ever matters.

How to read the score: it is a **regression check**, not a promise. The prompt and the rules were tuned against these same 48 cases, so the number overstates how the feature handles phrases nobody has tried, and 48 cases is a small sample. The real test is what people type in production.

## Testing

- **Unit tests** (`tests/test_ai.py`) mock `app.llm.call_tool` and never reach AWS: limits, errors, every normalisation rule, the Bedrock client against fake responses.
- **The eval set** (`python -m evals.run_eval`) runs the real model and scores it field by field (event or poll, dates, capacity, title, location, warnings), printing tokens, latency, estimated cost and, for a failure, **what the model actually answered**, to tell a model mistake from a rule mistake.
- `tests/test_eval_cases.py` checks the eval set itself (for example that "viernes 20" really is a Friday, and that a perfect model answer scores full marks through the code), so a mislabelled case cannot silently distort the measurement.

## Security and privacy

- **Prompt injection.** The user's text is wrapped in tags and declared data; the tool call is forced and schema-constrained, so there is no free text that could trigger an action; the output only prefills a form that the user reviews; and everything is validated in code. An eval case sends an injection attempt.
- **Least privilege.** The IAM user can only call `bedrock:InvokeModel` on one model. Its key lives in Render's environment, never in the repository (it is public). The policy matches the inference profile in any region, because the profile's ARN contains the region the call is made from, and pinning one failed with `AccessDenied` on the first real call.
- **Privacy.** The text is sent to AWS to draft the plan and is not stored; only counts and latency are. The privacy policy names AWS Bedrock as a provider.

## Known limits

- The eval set is small (48 cases) and the prompt was tuned against it, so its score overstates how it handles phrases nobody has tried. The real test is what people type in production.
- The hours chosen for each part of the day, and the decision that "que viene" means the nearest day, are product choices, not facts.
- There are no recurring events: recurring days become the options of a poll.
- It depends on one model in one provider. The model id is configuration, and the eval is how to compare another.

## Extending it

A new AI feature should reuse the pieces: call the model only through `app.llm.call_tool`, put it behind the same limits and logging in `app/routers/ai.py`, keep the rules in code, add cases to the eval set with **examples that do not repeat its inputs**, and mock the model in tests.

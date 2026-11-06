import { apiPost } from "./client";

// Codes from the backend; the UI turns them into text (aiPlan.warnings.*).
export type PlanWarning = "default_time" | "estimated_time" | "past_dates_dropped" | "no_dates" | "too_many_dates";

export interface PlanDraft {
  kind: "event" | "poll";
  title: string;
  description: string | null;
  location: string | null;
  duration_minutes: number;
  max_attendees: number | null;
  // ISO timestamps, ascending. One means an event; two or more mean a poll.
  dates: string[];
  warnings: PlanWarning[];
}

// What the create forms receive through the router state from the "Create with AI" screen.
export interface AiDraftState {
  aiDraft?: PlanDraft;
}

export function draftPlan(text: string): Promise<PlanDraft> {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return apiPost<PlanDraft>("/ai/plan-draft", { text, timezone });
}

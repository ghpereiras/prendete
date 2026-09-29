import { apiGet, apiPost, apiPut } from "./client";

export interface EventPollVoter {
  user_id: number;
  full_name: string;
  avatar_url: string | null;
}

export interface EventPollDateOption {
  id: number;
  starts_at: string;
  voters: EventPollVoter[];
  voted_by_me: boolean;
}

export interface EventPoll {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  location_details: string | null;
  maps_link: string | null;
  duration_minutes: number;
  owner_id: number;
  owner_name: string;
  resulting_event_id: number | null;
  date_options: EventPollDateOption[];
  created_at: string;
}

export interface EventPollCreateInput {
  title: string;
  description?: string;
  location?: string;
  location_details?: string;
  maps_link?: string;
  duration_minutes: number;
  date_options: string[];
}

export function listEventPolls(): Promise<EventPoll[]> {
  return apiGet<EventPoll[]>("/event-polls");
}

export function getEventPoll(id: number): Promise<EventPoll> {
  return apiGet<EventPoll>(`/event-polls/${id}`);
}

export function createEventPoll(data: EventPollCreateInput): Promise<EventPoll> {
  return apiPost<EventPoll>("/event-polls", data);
}

export function getPollInviteLink(pollId: number): Promise<{ invite_token: string }> {
  return apiGet<{ invite_token: string }>(`/event-polls/${pollId}/invite-link`);
}

export function regeneratePollInviteLink(pollId: number): Promise<{ invite_token: string }> {
  return apiPost<{ invite_token: string }>(`/event-polls/${pollId}/invite-link/regenerate`, {});
}

export interface EventPollDateOptionPreview {
  id: number;
  starts_at: string;
  vote_count: number;
}

export interface EventPollInvitePreview {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  location_details: string | null;
  maps_link: string | null;
  duration_minutes: number;
  owner_id: number;
  date_options: EventPollDateOptionPreview[];
}

export function previewPollInvite(token: string): Promise<EventPollInvitePreview> {
  return apiGet<EventPollInvitePreview>(`/event-polls/invite/${token}`);
}

export function votePollByInvite(token: string, optionIds: number[]): Promise<EventPoll> {
  return apiPost<EventPoll>(`/event-polls/invite/${token}/vote`, { option_ids: optionIds });
}

export function voteEventPoll(pollId: number, optionIds: number[]): Promise<EventPoll> {
  return apiPut<EventPoll>(`/event-polls/${pollId}/date-options/votes`, { option_ids: optionIds });
}

export function resolveEventPoll(
  pollId: number,
  resultingEventId: number,
  dateOptionId: number,
): Promise<EventPoll> {
  return apiPost<EventPoll>(`/event-polls/${pollId}/resolve`, {
    resulting_event_id: resultingEventId,
    date_option_id: dateOptionId,
  });
}

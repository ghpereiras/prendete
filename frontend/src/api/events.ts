import { apiGet, apiPost } from "./client";

export interface Event {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  starts_at: string;
  ends_at: string;
  max_attendees: number;
  owner_id: number;
  created_at: string;
}

export interface EventCreateInput {
  title: string;
  description?: string;
  location?: string;
  starts_at: string;
  ends_at: string;
  max_attendees: number;
}

export function listEvents(): Promise<Event[]> {
  return apiGet<Event[]>("/events");
}

export function getEvent(id: number): Promise<Event> {
  return apiGet<Event>(`/events/${id}`);
}

export function createEvent(data: EventCreateInput): Promise<Event> {
  return apiPost<Event>("/events", data);
}

export function getInviteLink(eventId: number): Promise<{ invite_token: string }> {
  return apiGet<{ invite_token: string }>(`/events/${eventId}/invite-link`);
}

export interface EventInvitePreview {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  starts_at: string;
  ends_at: string;
  max_attendees: number;
  spots_left: number;
}

export function previewInvite(token: string): Promise<EventInvitePreview> {
  return apiGet<EventInvitePreview>(`/events/invite/${token}`);
}

export interface Invitation {
  id: number;
  event_id: number;
  invitee_id: number;
  status: "pending" | "accepted" | "declined";
  invited_at: string;
  responded_at: string | null;
}

export function joinEvent(token: string): Promise<Invitation> {
  return apiPost<Invitation>(`/events/invite/${token}/join`, {});
}

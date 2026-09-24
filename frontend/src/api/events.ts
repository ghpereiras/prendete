import { apiGet, apiPost } from "./client";

export interface Event {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  location_details: string | null;
  maps_link: string | null;
  starts_at: string;
  duration_minutes: number;
  registration_deadline_minutes_before: number | null;
  max_attendees: number;
  owner_id: number;
  created_at: string;
}

export interface EventCreateInput {
  title: string;
  description?: string;
  location?: string;
  location_details?: string;
  maps_link?: string;
  starts_at: string;
  duration_minutes: number;
  registration_deadline_minutes_before?: number;
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

export interface EventAttendee {
  user_id: number;
  full_name: string;
  email: string;
  is_owner: boolean;
  comment: string | null;
}

export function listAttendees(eventId: number): Promise<EventAttendee[]> {
  return apiGet<EventAttendee[]>(`/events/${eventId}/attendees`);
}

export interface EventInvitePreview {
  id: number;
  title: string;
  description: string | null;
  location: string | null;
  location_details: string | null;
  maps_link: string | null;
  starts_at: string;
  duration_minutes: number;
  registration_deadline_minutes_before: number | null;
  max_attendees: number;
  spots_left: number;
  registration_open: boolean;
  owner_id: number;
}

export function previewInvite(token: string): Promise<EventInvitePreview> {
  return apiGet<EventInvitePreview>(`/events/invite/${token}`);
}

export interface Invitation {
  id: number;
  event_id: number;
  invitee_id: number;
  status: "pending" | "accepted" | "declined";
  comment: string | null;
  invited_at: string;
  responded_at: string | null;
}

export function joinEvent(token: string, comment?: string): Promise<Invitation> {
  return apiPost<Invitation>(`/events/invite/${token}/join`, { comment: comment || undefined });
}

export function endsAt(startsAt: string, durationMinutes: number): Date {
  return new Date(new Date(startsAt).getTime() + durationMinutes * 60000);
}

// Without an explicit deadline, registration closes when the event starts.
export function registrationDeadline(
  startsAt: string,
  registrationDeadlineMinutesBefore: number | null,
): Date {
  const minutesBefore = registrationDeadlineMinutesBefore ?? 0;
  return new Date(new Date(startsAt).getTime() - minutesBefore * 60000);
}

export function isRegistrationOpen(
  startsAt: string,
  registrationDeadlineMinutesBefore: number | null,
): boolean {
  return Date.now() < registrationDeadline(startsAt, registrationDeadlineMinutesBefore).getTime();
}

import { apiDelete, apiGet, apiPatch, apiPost } from "./client";

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
  owner_name: string;
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

export function updateEvent(id: number, data: EventCreateInput): Promise<Event> {
  return apiPatch<Event>(`/events/${id}`, data);
}

export function deleteEvent(id: number): Promise<void> {
  return apiDelete<void>(`/events/${id}`);
}

export function getInviteLink(eventId: number): Promise<{ invite_token: string }> {
  return apiGet<{ invite_token: string }>(`/events/${eventId}/invite-link`);
}

export interface EventAttendee {
  user_id: number;
  full_name: string;
  email: string;
  avatar_url: string | null;
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

export interface Attendance {
  id: number;
  event_id: number;
  user_id: number;
  comment: string | null;
  joined_at: string;
}

export function joinEvent(token: string, comment?: string): Promise<Attendance> {
  return apiPost<Attendance>(`/events/invite/${token}/join`, { comment: comment || undefined });
}

export function updateAttendance(eventId: number, comment: string | null): Promise<Attendance> {
  return apiPatch<Attendance>(`/events/${eventId}/attendance`, { comment });
}

export function leaveEvent(eventId: number): Promise<void> {
  return apiDelete<void>(`/events/${eventId}/attendance`);
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

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import {
  endsAt,
  getEvent,
  getInviteLink,
  isRegistrationOpen,
  listAttendees,
  registrationDeadline,
  type Event,
  type EventAttendee,
} from "../api/events";
import EventLocation from "../components/EventLocation";

export default function EventDetail() {
  const { t } = useTranslation();
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<Event | null>(null);
  const [attendees, setAttendees] = useState<EventAttendee[] | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) return;
    getEvent(Number(eventId))
      .then(setEvent)
      .catch(() => setError(t("eventDetail.notFound")));
  }, [eventId, t]);

  useEffect(() => {
    if (!eventId || !event) return;
    listAttendees(Number(eventId)).then(setAttendees);
  }, [eventId, event]);

  useEffect(() => {
    if (!eventId || !event) return;
    getInviteLink(Number(eventId))
      .then(({ invite_token }) => setInviteUrl(`${window.location.origin}/invite/${invite_token}`))
      .catch((err) => {
        // Non-owners can't fetch the invite link; that's expected, not an error to show.
        if (!(err instanceof ApiError && err.status === 403)) {
          setError(t("eventDetail.linkError"));
        }
      });
  }, [eventId, event, t]);

  async function copyLink() {
    if (!inviteUrl) return;
    await navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (error) {
    return (
      <div className="page">
        <p className="error">{error}</p>
        <Link to="/">{t("eventDetail.backHome")}</Link>
      </div>
    );
  }

  if (!event) {
    return <p className="page">{t("common.loading")}</p>;
  }

  const acceptedCount = attendees ? attendees.filter((a) => !a.is_owner).length : null;
  const spotsLeft = acceptedCount === null ? null : Math.max(event.max_attendees - acceptedCount, 0);

  return (
    <div className="page">
      <h1>{event.title}</h1>
      {event.description && <p>{event.description}</p>}
      <EventLocation
        location={event.location}
        locationDetails={event.location_details}
        mapsLink={event.maps_link}
      />
      <p>
        {new Date(event.starts_at).toLocaleString()} —{" "}
        {endsAt(event.starts_at, event.duration_minutes).toLocaleString()}
      </p>
      <p>
        {spotsLeft === null
          ? t("common.loading")
          : t("eventDetail.spotsLeft", { count: spotsLeft })}
      </p>
      {event.registration_deadline_minutes_before !== null && (
        <p className={isRegistrationOpen(event.starts_at, event.registration_deadline_minutes_before) ? undefined : "error"}>
          {isRegistrationOpen(event.starts_at, event.registration_deadline_minutes_before)
            ? t("eventDetail.registrationDeadline", {
                date: registrationDeadline(
                  event.starts_at,
                  event.registration_deadline_minutes_before,
                )!.toLocaleString(),
              })
            : t("eventDetail.registrationClosed")}
        </p>
      )}

      {inviteUrl && (
        <div className="invite-link">
          <p>{t("eventDetail.shareLink")}</p>
          <code>{inviteUrl}</code>
          <button onClick={copyLink}>
            {copied ? t("eventDetail.copied") : t("eventDetail.copy")}
          </button>
        </div>
      )}

      {attendees && attendees.length > 0 && (
        <div className="attendee-list">
          <p>{t("eventDetail.attendees")}</p>
          <ul>
            {attendees.map((attendee) => (
              <li key={attendee.user_id}>
                {attendee.full_name}
                {attendee.is_owner && (
                  <span className="owner-badge">{t("eventDetail.ownerBadge")}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Link to="/">{t("eventDetail.backHome")}</Link>
    </div>
  );
}

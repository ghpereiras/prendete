import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getEvent, getInviteLink, type Event } from "../api/events";

export default function EventDetail() {
  const { t } = useTranslation();
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<Event | null>(null);
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

  return (
    <div className="page">
      <h1>{event.title}</h1>
      {event.description && <p>{event.description}</p>}
      {event.location && <p>{event.location}</p>}
      <p>
        {new Date(event.starts_at).toLocaleString()} — {new Date(event.ends_at).toLocaleString()}
      </p>
      <p>{t("eventDetail.maxAttendees", { count: event.max_attendees })}</p>

      {inviteUrl && (
        <div className="invite-link">
          <p>{t("eventDetail.shareLink")}</p>
          <code>{inviteUrl}</code>
          <button onClick={copyLink}>
            {copied ? t("eventDetail.copied") : t("eventDetail.copy")}
          </button>
        </div>
      )}

      <Link to="/">{t("eventDetail.backHome")}</Link>
    </div>
  );
}

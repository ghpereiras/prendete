import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import {
  endsAt,
  joinEvent,
  previewInvite,
  registrationDeadline,
  type EventInvitePreview,
} from "../api/events";
import EventLocation from "../components/EventLocation";
import { useAuth } from "../context/AuthContext";
import { useCountdown } from "../hooks/useCountdown";
import { formatCountdown } from "../utils/time";

export default function InvitePreview() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [event, setEvent] = useState<EventInvitePreview | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    if (!token) return;
    previewInvite(token)
      .then(setEvent)
      .catch(() => setNotFound(true));
  }, [token]);

  const deadline = event
    ? registrationDeadline(event.starts_at, event.registration_deadline_minutes_before)
    : null;
  const { msRemaining, isOver } = useCountdown(deadline);
  const registrationClosed = isOver;

  async function handleJoin() {
    if (!token) return;
    setJoinError(null);
    setJoining(true);
    try {
      const invitation = await joinEvent(token);
      navigate(`/events/${invitation.event_id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setJoinError(t("invitePreview.alreadyJoinedOrFull"));
      } else {
        setJoinError(t("invitePreview.joinError"));
      }
    } finally {
      setJoining(false);
    }
  }

  if (notFound) {
    return (
      <div className="page">
        <p className="error">{t("invitePreview.notFound")}</p>
        <Link to="/">{t("eventDetail.backHome")}</Link>
      </div>
    );
  }

  if (!event) {
    return <p className="page">{t("common.loading")}</p>;
  }

  const isOwner = user?.id === event.owner_id;
  const isFull = event.spots_left <= 0;

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
        {isFull
          ? t("invitePreview.full")
          : t("invitePreview.spotsLeft", { count: event.spots_left })}
      </p>

      {registrationClosed ? (
        <p className="error">{t("invitePreview.registrationClosed")}</p>
      ) : (
        <p className="countdown">
          {t("invitePreview.timeToRegister", { time: formatCountdown(msRemaining) })}
        </p>
      )}

      {joinError && <p className="error">{joinError}</p>}

      {isOwner ? (
        <p>{t("invitePreview.isOwner")}</p>
      ) : registrationClosed ? null : user ? (
        <button onClick={handleJoin} disabled={joining || isFull}>
          {joining ? t("invitePreview.joining") : t("invitePreview.join")}
        </button>
      ) : (
        <div className="invite-auth-prompt">
          <p>{t("invitePreview.needsAuth")}</p>
          <Link
            className="button-link"
            to="/login"
            state={{ from: `/invite/${token}` }}
          >
            {t("login.title")}
          </Link>
          <Link to="/register" state={{ from: `/invite/${token}` }}>
            {t("login.registerLink")}
          </Link>
        </div>
      )}
    </div>
  );
}

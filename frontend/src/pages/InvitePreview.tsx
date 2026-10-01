import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, isServerUnavailable, loadWhileServerWakes } from "../api/client";
import {
  endsAt,
  joinEvent,
  previewInvite,
  registrationDeadline,
  type EventInvitePreview,
} from "../api/events";
import EventLocation from "../components/EventLocation";
import LoadingPage from "../components/LoadingPage";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";
import { useCountdown } from "../hooks/useCountdown";
import { formatDateTime } from "../utils/date";
import { formatCountdown } from "../utils/time";

export default function InvitePreview() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";
  const { token } = useParams<{ token: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [event, setEvent] = useState<EventInvitePreview | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [slow, setSlow] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);
  const [comment, setComment] = useState("");

  usePageTitle(event?.title ?? (notFound ? t("invitePreview.notFound") : t("common.loading")));

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    loadWhileServerWakes(() => previewInvite(token), {
      onSlow: () => setSlow(true),
      isCancelled: () => cancelled,
    })
      .then(setEvent)
      .catch((err) => {
        if (cancelled) return;
        if (isServerUnavailable(err)) setUnavailable(true);
        else setNotFound(true);
      });
    return () => {
      cancelled = true;
    };
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
      const attendance = await joinEvent(token, comment);
      navigate(`/events/${attendance.event_id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setJoinError("invitePreview.alreadyJoinedOrFull");
      } else {
        setJoinError("invitePreview.joinError");
      }
    } finally {
      setJoining(false);
    }
  }

  if (notFound || unavailable) {
    return (
      <div className="page">
        <p className="error">{t(unavailable ? "common.serverUnavailable" : "invitePreview.notFound")}</p>
      </div>
    );
  }

  if (!event) {
    return <LoadingPage slow={slow} />;
  }

  const isOwner = user?.id === event.owner_id;
  const isFull = event.spots_left !== null && event.spots_left <= 0;

  return (
    <div className="page">
      {event.description && <p>{event.description}</p>}
      <EventLocation
        location={event.location}
        locationDetails={event.location_details}
        mapsLink={event.maps_link}
      />
      <p>
        {formatDateTime(event.starts_at, lang)} —{" "}
        {formatDateTime(endsAt(event.starts_at, event.duration_minutes), lang)}
      </p>
      <p>
        {isFull
          ? t("invitePreview.full")
          : event.spots_left === null
            ? t("invitePreview.unlimitedSpots")
            : t("invitePreview.spotsLeft", { count: event.spots_left })}
      </p>

      {registrationClosed ? (
        <p className="error">{t("invitePreview.registrationClosed")}</p>
      ) : (
        <p className="countdown">
          {t("invitePreview.timeToRegister", { time: formatCountdown(msRemaining) })}
        </p>
      )}

      {joinError && <p className="error">{t(joinError)}</p>}

      {isOwner ? (
        <p>{t("invitePreview.isOwner")}</p>
      ) : registrationClosed ? null : user ? (
        <div className="join-form">
          <label className="sr-only" htmlFor="join-comment">
            {t("invitePreview.commentLabel")}
          </label>
          <textarea
            id="join-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t("invitePreview.commentPlaceholder")}
            rows={2}
            maxLength={500}
          />
          <button onClick={handleJoin} disabled={joining || isFull}>
            {joining ? t("invitePreview.joining") : t("invitePreview.join")}
          </button>
        </div>
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

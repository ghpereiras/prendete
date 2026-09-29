import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { avatarUrl, ApiError } from "../api/client";
import { createEvent, getEvent, isRegistrationOpen, updateEvent } from "../api/events";
import { resolveEventPoll, type EventPollVoter } from "../api/eventPolls";
import Avatar from "../components/Avatar";
import EventLocation from "../components/EventLocation";
import LocationSearch from "../components/LocationSearch";
import { usePageTitle } from "../context/PageTitleContext";
import { toDatetimeLocalValue } from "../utils/date";

interface FromPoll {
  pollId: number;
  dateOptionId: number;
  title: string;
  description: string | null;
  location: string | null;
  locationDetails: string | null;
  mapsLink: string | null;
  durationMinutes: number;
  startsAt: string;
  voters: EventPollVoter[];
}

interface FieldErrors {
  title?: string;
  startsAt?: string;
  durationHours?: string;
  maxAttendees?: string;
  registrationDeadlineHours?: string;
}

export default function CreateEvent() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const routerLocation = useLocation();
  const { eventId } = useParams<{ eventId: string }>();
  const isEditing = Boolean(eventId);
  const fromPoll = (routerLocation.state as { fromPoll?: FromPoll } | null)?.fromPoll ?? null;
  const [title, setTitle] = useState(fromPoll?.title ?? "");
  const [description, setDescription] = useState(fromPoll?.description ?? "");
  const [location, setLocation] = useState(fromPoll?.location ?? "");
  const [locationDetails, setLocationDetails] = useState(fromPoll?.locationDetails ?? "");
  const [mapsLink, setMapsLink] = useState(fromPoll?.mapsLink ?? "");
  const [startsAt, setStartsAt] = useState(
    fromPoll ? toDatetimeLocalValue(new Date(fromPoll.startsAt)) : "",
  );
  const [durationHours, setDurationHours] = useState(
    fromPoll ? String(fromPoll.durationMinutes / 60) : "3",
  );
  const [registrationDeadlineHours, setRegistrationDeadlineHours] = useState("");
  const [limitAttendees, setLimitAttendees] = useState(false);
  const [maxAttendees, setMaxAttendees] = useState("10");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(isEditing);
  const [confirmingNotify, setConfirmingNotify] = useState(false);

  usePageTitle(t(isEditing ? "createEvent.editTitle" : "createEvent.title"));

  useEffect(() => {
    if (!eventId) return;
    getEvent(Number(eventId))
      .then((event) => {
        setTitle(event.title);
        setDescription(event.description ?? "");
        setLocation(event.location ?? "");
        setLocationDetails(event.location_details ?? "");
        setMapsLink(event.maps_link ?? "");
        setStartsAt(toDatetimeLocalValue(new Date(event.starts_at)));
        setDurationHours(String(event.duration_minutes / 60));
        setRegistrationDeadlineHours(
          event.registration_deadline_minutes_before
            ? String(event.registration_deadline_minutes_before / 60)
            : "",
        );
        setLimitAttendees(event.max_attendees !== null);
        if (event.max_attendees !== null) {
          setMaxAttendees(String(event.max_attendees));
        }
      })
      .catch(() => setLoadError("createEvent.editLoadError"))
      .finally(() => setLoading(false));
  }, [eventId]);

  function validate(): FieldErrors {
    const errors: FieldErrors = {};

    if (!title.trim()) {
      errors.title = "createEvent.errorTitleRequired";
    }

    let startsAtIso: string | null = null;
    if (!startsAt) {
      errors.startsAt = "createEvent.errorStartsAtRequired";
    } else {
      startsAtIso = new Date(startsAt).toISOString();
      if (new Date(startsAtIso).getTime() <= Date.now()) {
        errors.startsAt = "createEvent.errorStartsInPast";
      }
    }

    const durationValue = Number(durationHours);
    if (!durationHours || Number.isNaN(durationValue) || durationValue <= 0) {
      errors.durationHours = "createEvent.errorDurationRequired";
    }

    if (limitAttendees) {
      const maxAttendeesValue = Number(maxAttendees);
      if (!maxAttendees || Number.isNaN(maxAttendeesValue) || maxAttendeesValue <= 0) {
        errors.maxAttendees = "createEvent.errorMaxAttendeesRequired";
      }
    }

    if (startsAtIso && !errors.startsAt) {
      const registrationDeadlineMinutes = registrationDeadlineHours
        ? Math.round(Number(registrationDeadlineHours) * 60)
        : null;
      if (!isRegistrationOpen(startsAtIso, registrationDeadlineMinutes)) {
        errors.registrationDeadlineHours = "createEvent.errorRegistrationAlreadyClosed";
      }
    }

    return errors;
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    if (isEditing) {
      setConfirmingNotify(true);
      return;
    }

    void save(false);
  }

  async function save(notifyAttendees: boolean) {
    const startsAtIso = new Date(startsAt).toISOString();
    const registrationDeadlineMinutes = registrationDeadlineHours
      ? Math.round(Number(registrationDeadlineHours) * 60)
      : null;

    const payload = {
      title,
      description: description || undefined,
      location: location || undefined,
      location_details: locationDetails || undefined,
      maps_link: mapsLink || undefined,
      starts_at: startsAtIso,
      duration_minutes: Math.round(Number(durationHours) * 60),
      registration_deadline_minutes_before: registrationDeadlineMinutes ?? undefined,
      max_attendees: limitAttendees ? Number(maxAttendees) : null,
    };

    setConfirmingNotify(false);
    setSubmitting(true);
    try {
      const event = isEditing
        ? await updateEvent(Number(eventId), payload, notifyAttendees)
        : await createEvent(payload);
      if (fromPoll) {
        await resolveEventPoll(fromPoll.pollId, event.id, fromPoll.dateOptionId);
      }
      navigate(`/events/${event.id}`);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError && err.status === 422
          ? "createEvent.errorMaxAttendeesBelowAccepted"
          : "createEvent.error",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const hasFieldErrors = Object.keys(fieldErrors).length > 0;

  if (loading) {
    return <p className="page">{t("common.loading")}</p>;
  }

  if (loadError) {
    return (
      <div className="page">
        <p className="error">{t(loadError)}</p>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {fromPoll && fromPoll.voters.length > 0 && (
          <div className="poll-voters-box">
            <p>{t("createEvent.pollVotersLabel")}</p>
            <div className="poll-voters-list">
              {fromPoll.voters.map((voter) => (
                <span key={voter.user_id} className="poll-voter">
                  <Avatar avatarUrl={avatarUrl(voter.avatar_url)} fullName={voter.full_name} />
                  {voter.full_name}
                </span>
              ))}
            </div>
          </div>
        )}
        <label>
          {t("createEvent.name")}
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
          {fieldErrors.title && <span className="field-error">{t(fieldErrors.title)}</span>}
        </label>
        <label>
          {t("createEvent.description")}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </label>
        <LocationSearch
          value={location}
          onQueryChange={(value) => {
            setLocation(value);
            setMapsLink("");
          }}
          onSelect={(result) => {
            setLocation(result.name);
            setMapsLink(result.mapsLink);
          }}
        />
        <label>
          {t("createEvent.locationDetails")}
          <input
            type="text"
            value={locationDetails}
            onChange={(e) => setLocationDetails(e.target.value)}
            placeholder={t("createEvent.locationDetailsPlaceholder")}
          />
        </label>
        <EventLocation location={location || null} locationDetails={locationDetails || null} mapsLink={mapsLink || null} />
        <label>
          {t("createEvent.startsAt")}
          <input
            type="datetime-local"
            value={startsAt}
            onChange={(e) => setStartsAt(e.target.value)}
            min={toDatetimeLocalValue(new Date())}
          />
          {fieldErrors.startsAt && <span className="field-error">{t(fieldErrors.startsAt)}</span>}
        </label>
        <label>
          {t("createEvent.durationHours")}
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={durationHours}
            onChange={(e) => setDurationHours(e.target.value)}
          />
          {fieldErrors.durationHours && (
            <span className="field-error">{t(fieldErrors.durationHours)}</span>
          )}
        </label>
        <label>
          {t("createEvent.registrationDeadlineHours")}
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={registrationDeadlineHours}
            onChange={(e) => setRegistrationDeadlineHours(e.target.value)}
            placeholder={t("createEvent.registrationDeadlinePlaceholder")}
          />
          <span className="field-hint">{t("createEvent.registrationDeadlineHint")}</span>
          {fieldErrors.registrationDeadlineHours && (
            <span className="field-error">{t(fieldErrors.registrationDeadlineHours)}</span>
          )}
        </label>
        <div className="toggle-row">
          <span>{t("createEvent.maxAttendees")}</span>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={limitAttendees}
              onChange={(e) => setLimitAttendees(e.target.checked)}
            />
            <span className="toggle-slider" />
          </label>
        </div>
        {limitAttendees && (
          <label>
            <span className="sr-only">{t("createEvent.maxAttendees")}</span>
            <input
              type="number"
              min={1}
              value={maxAttendees}
              onChange={(e) => setMaxAttendees(e.target.value)}
            />
            {fieldErrors.maxAttendees && (
              <span className="field-error">{t(fieldErrors.maxAttendees)}</span>
            )}
          </label>
        )}
        <button type="submit" disabled={submitting}>
          {submitting
            ? t(isEditing ? "createEvent.editSubmitting" : "createEvent.submitting")
            : t(isEditing ? "createEvent.editSubmit" : "createEvent.submit")}
        </button>
        {submitError ? (
          <p className="error">{t(submitError)}</p>
        ) : (
          hasFieldErrors && <p className="error">{t("createEvent.hasErrors")}</p>
        )}
      </form>

      {confirmingNotify && (
        <div
          className="confirm-modal-backdrop"
          onClick={() => {
            if (!submitting) setConfirmingNotify(false);
          }}
        >
          <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
            <p>{t("createEvent.notifyAttendeesPrompt")}</p>
            <div className="confirm-modal-actions">
              <button type="button" onClick={() => save(false)} disabled={submitting}>
                {t("createEvent.notifyAttendeesDecline")}
              </button>
              <button type="button" onClick={() => save(true)} disabled={submitting}>
                {submitting
                  ? t("createEvent.editSubmitting")
                  : t("createEvent.notifyAttendeesConfirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

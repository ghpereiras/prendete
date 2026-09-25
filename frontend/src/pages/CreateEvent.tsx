import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { createEvent, getEvent, isRegistrationOpen, updateEvent } from "../api/events";
import EventLocation from "../components/EventLocation";
import LocationSearch from "../components/LocationSearch";
import { usePageTitle } from "../context/PageTitleContext";

function toDatetimeLocalValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
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
  const { eventId } = useParams<{ eventId: string }>();
  const isEditing = Boolean(eventId);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [locationDetails, setLocationDetails] = useState("");
  const [mapsLink, setMapsLink] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [durationHours, setDurationHours] = useState("3");
  const [registrationDeadlineHours, setRegistrationDeadlineHours] = useState("");
  const [maxAttendees, setMaxAttendees] = useState("10");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(isEditing);

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
        setMaxAttendees(String(event.max_attendees));
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

    const maxAttendeesValue = Number(maxAttendees);
    if (!maxAttendees || Number.isNaN(maxAttendeesValue) || maxAttendeesValue <= 0) {
      errors.maxAttendees = "createEvent.errorMaxAttendeesRequired";
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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

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
      max_attendees: Number(maxAttendees),
    };

    setSubmitting(true);
    try {
      const event = isEditing ? await updateEvent(Number(eventId), payload) : await createEvent(payload);
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
        <label>
          {t("createEvent.maxAttendees")}
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
    </div>
  );
}

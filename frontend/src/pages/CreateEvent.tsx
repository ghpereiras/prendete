import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { createEvent } from "../api/events";

export default function CreateEvent() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [locationDetails, setLocationDetails] = useState("");
  const [mapsLink, setMapsLink] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [durationHours, setDurationHours] = useState("3");
  const [registrationDeadlineHours, setRegistrationDeadlineHours] = useState("");
  const [maxAttendees, setMaxAttendees] = useState("10");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const event = await createEvent({
        title,
        description: description || undefined,
        location: location || undefined,
        location_details: locationDetails || undefined,
        maps_link: mapsLink || undefined,
        starts_at: new Date(startsAt).toISOString(),
        duration_minutes: Math.round(Number(durationHours) * 60),
        registration_deadline_minutes_before: registrationDeadlineHours
          ? Math.round(Number(registrationDeadlineHours) * 60)
          : undefined,
        max_attendees: Number(maxAttendees),
      });
      navigate(`/events/${event.id}`);
    } catch {
      setError(t("createEvent.error"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>{t("createEvent.title")}</h1>
        {error && <p className="error">{error}</p>}
        <label>
          {t("createEvent.name")}
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          {t("createEvent.description")}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </label>
        <label>
          {t("createEvent.location")}
          <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} />
        </label>
        <label>
          {t("createEvent.locationDetails")}
          <input
            type="text"
            value={locationDetails}
            onChange={(e) => setLocationDetails(e.target.value)}
            placeholder={t("createEvent.locationDetailsPlaceholder")}
          />
        </label>
        <label>
          {t("createEvent.mapsLink")}
          <input
            type="url"
            value={mapsLink}
            onChange={(e) => setMapsLink(e.target.value)}
            placeholder="https://www.google.com/maps/..."
          />
          <span className="field-hint">{t("createEvent.mapsLinkHint")}</span>
        </label>
        <label>
          {t("createEvent.startsAt")}
          <input
            type="datetime-local"
            value={startsAt}
            onChange={(e) => setStartsAt(e.target.value)}
            required
          />
        </label>
        <label>
          {t("createEvent.durationHours")}
          <input
            type="number"
            min={0.5}
            step={0.5}
            value={durationHours}
            onChange={(e) => setDurationHours(e.target.value)}
            required
          />
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
        </label>
        <label>
          {t("createEvent.maxAttendees")}
          <input
            type="number"
            min={1}
            value={maxAttendees}
            onChange={(e) => setMaxAttendees(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? t("createEvent.submitting") : t("createEvent.submit")}
        </button>
      </form>
    </div>
  );
}

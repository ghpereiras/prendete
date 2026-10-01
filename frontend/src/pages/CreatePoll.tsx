import { useState, type FormEvent, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { createEventPoll } from "../api/eventPolls";
import DateTimeField from "../components/DateTimeField";
import EventLocation from "../components/EventLocation";
import LocationSearch from "../components/LocationSearch";
import { usePageTitle } from "../context/PageTitleContext";
import { toDatetimeLocalValue } from "../utils/date";

interface FieldErrors {
  title?: string;
  durationHours?: string;
  dateOptions?: string;
}

function defaultDateOptions(): string[] {
  return ["", ""];
}

export default function CreatePoll() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [locationDetails, setLocationDetails] = useState("");
  const [mapsLink, setMapsLink] = useState("");
  const [durationHours, setDurationHours] = useState("3");
  const [dateOptions, setDateOptions] = useState<string[]>(defaultDateOptions());
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  usePageTitle(t("createPoll.title"));

  function setDateOption(index: number, value: string) {
    setDateOptions((prev) => prev.map((option, i) => (i === index ? value : option)));
  }

  function addDateOption() {
    setDateOptions((prev) => [...prev, ""]);
  }

  function removeDateOption(index: number) {
    setDateOptions((prev) => prev.filter((_, i) => i !== index));
  }

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!title.trim()) {
      errors.title = "createPoll.errorTitleRequired";
    }

    const durationValue = Number(durationHours);
    if (!durationHours || Number.isNaN(durationValue) || durationValue <= 0) {
      errors.durationHours = "createPoll.errorDurationRequired";
    }

    const filled = dateOptions.filter((value) => value);
    if (filled.length < 2) {
      errors.dateOptions = "createPoll.errorAtLeastTwoDates";
    } else {
      const isoValues = filled.map((value) => new Date(value).toISOString());
      if (isoValues.some((iso) => new Date(iso).getTime() <= Date.now())) {
        errors.dateOptions = "createPoll.errorDatesInPast";
      } else if (new Set(isoValues).size !== isoValues.length) {
        errors.dateOptions = "createPoll.errorDuplicateDates";
      }
    }

    return errors;
  }

  function blockEnterSubmit(e: KeyboardEvent<HTMLFormElement>) {
    if (e.key === "Enter" && !(e.target instanceof HTMLTextAreaElement)) {
      e.preventDefault();
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    const payload = {
      title,
      description: description || undefined,
      location: location || undefined,
      location_details: locationDetails || undefined,
      maps_link: mapsLink || undefined,
      duration_minutes: Math.round(Number(durationHours) * 60),
      date_options: dateOptions
        .filter((value) => value)
        .map((value) => new Date(value).toISOString()),
    };

    setSubmitting(true);
    try {
      const poll = await createEventPoll(payload);
      navigate(`/polls/${poll.id}`);
    } catch {
      setSubmitError("createPoll.error");
    } finally {
      setSubmitting(false);
    }
  }

  const hasFieldErrors = Object.keys(fieldErrors).length > 0;

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit} onKeyDown={blockEnterSubmit} noValidate>
        <label>
          {t("createPoll.name")}
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
          {fieldErrors.title && <span className="field-error">{t(fieldErrors.title)}</span>}
        </label>
        <label>
          {t("createPoll.description")}
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
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
          {t("createPoll.locationDetails")}
          <input
            type="text"
            value={locationDetails}
            onChange={(e) => setLocationDetails(e.target.value)}
            placeholder={t("createPoll.locationDetailsPlaceholder")}
          />
        </label>
        <EventLocation location={location || null} locationDetails={locationDetails || null} mapsLink={mapsLink || null} />
        <label>
          {t("createPoll.durationHours")}
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

        <div className="poll-date-options">
          <p>{t("createPoll.dateOptionsLabel")}</p>
          {dateOptions.map((value, index) => (
            <div key={index} className="poll-date-option-row">
              <DateTimeField
                value={value}
                onChange={(v) => setDateOption(index, v)}
                min={toDatetimeLocalValue(new Date())}
              />
              {dateOptions.length > 2 && (
                <button type="button" onClick={() => removeDateOption(index)}>
                  {t("createPoll.removeDate")}
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addDateOption} className="poll-add-date">
            {t("createPoll.addDate")}
          </button>
          {fieldErrors.dateOptions && (
            <span className="field-error">{t(fieldErrors.dateOptions)}</span>
          )}
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? t("createPoll.submitting") : t("createPoll.submit")}
        </button>
        {submitError ? (
          <p className="error">{t(submitError)}</p>
        ) : (
          hasFieldErrors && <p className="error">{t("createPoll.hasErrors")}</p>
        )}
      </form>
    </div>
  );
}

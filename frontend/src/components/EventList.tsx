import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { Event } from "../api/events";
import { formatDateTime } from "../utils/date";

interface EventListProps {
  events: Event[];
  emptyMessage: string;
}

export default function EventList({ events, emptyMessage }: EventListProps) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";

  if (events.length === 0) {
    return <p>{emptyMessage}</p>;
  }

  return (
    <div className="event-list">
      {events.map((event) => (
        <Link key={event.id} to={`/events/${event.id}`} className="event-list-item">
          <div className="event-list-title">{event.title}</div>
          <div className="event-list-meta">
            {formatDateTime(event.starts_at, lang)} ·{" "}
            {t("home.organizedBy", { name: event.owner_name })}
          </div>
        </Link>
      ))}
    </div>
  );
}

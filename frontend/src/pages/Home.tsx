import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { listEvents, type Event } from "../api/events";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    listEvents().then(setEvents);
  }, []);

  return (
    <div className="page">
      <h1>{t("home.greeting", { name: user?.full_name })}</h1>
      <p>{user?.email}</p>
      <button onClick={logout}>{t("home.logout")}</button>

      <Link to="/events/new" className="button-link">
        {t("home.createEvent")}
      </Link>

      <div className="event-list">
        {events.length === 0 && <p>{t("home.noEvents")}</p>}
        {events.map((event) => (
          <Link key={event.id} to={`/events/${event.id}`} className="event-list-item">
            {event.title}
          </Link>
        ))}
      </div>
    </div>
  );
}

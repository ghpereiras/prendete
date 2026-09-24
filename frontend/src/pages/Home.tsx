import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { listEvents, type Event } from "../api/events";
import EventList from "../components/EventList";
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

      <EventList events={events} emptyMessage={t("home.noEvents")} />
    </div>
  );
}

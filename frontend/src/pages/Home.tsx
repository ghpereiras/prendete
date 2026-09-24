import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { listEvents, type Event } from "../api/events";
import EventList from "../components/EventList";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

export default function Home() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [events, setEvents] = useState<Event[]>([]);

  usePageTitle(t("home.greeting", { name: user?.full_name }));

  useEffect(() => {
    listEvents().then(setEvents);
  }, []);

  return (
    <div className="page">
      <Link to="/events/new" className="button-link">
        {t("home.createEvent")}
      </Link>

      <EventList events={events} emptyMessage={t("home.noEvents")} />
    </div>
  );
}

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { listEvents, type Event } from "../api/events";
import EventList from "../components/EventList";

export default function PastEvents() {
  const { t } = useTranslation();
  const [events, setEvents] = useState<Event[] | null>(null);

  useEffect(() => {
    listEvents().then((all) => {
      const now = Date.now();
      // Most recently finished event first.
      setEvents(all.filter((event) => new Date(event.starts_at).getTime() < now).reverse());
    });
  }, []);

  return (
    <div className="page">
      <h1>{t("sidebar.past")}</h1>
      {events === null ? (
        <p>{t("common.loading")}</p>
      ) : (
        <EventList events={events} emptyMessage={t("pastEvents.empty")} />
      )}
    </div>
  );
}

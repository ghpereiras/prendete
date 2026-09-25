import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { listEvents, type Event } from "../api/events";
import EventList from "../components/EventList";
import SegmentedFilter from "../components/SegmentedFilter";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

type TimeFilterValue = "upcoming" | "past";
type OwnerFilterValue = "all" | "mine" | "others";

export default function Events() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [events, setEvents] = useState<Event[] | null>(null);
  const [timeFilter, setTimeFilter] = useState<TimeFilterValue>("upcoming");
  const [ownerFilter, setOwnerFilter] = useState<OwnerFilterValue>("all");

  usePageTitle(t("home.greeting", { name: user?.full_name }));

  useEffect(() => {
    listEvents().then(setEvents);
  }, []);

  const now = Date.now();
  const timeFiltered = events?.filter((event) =>
    timeFilter === "upcoming"
      ? new Date(event.starts_at).getTime() >= now
      : new Date(event.starts_at).getTime() < now,
  );
  // Soonest first for upcoming, most recently finished first for past.
  const ordered = timeFilter === "past" ? timeFiltered?.reverse() : timeFiltered;
  const filteredEvents = ordered?.filter((event) => {
    if (ownerFilter === "mine") return event.owner_id === user?.id;
    if (ownerFilter === "others") return event.owner_id !== user?.id;
    return true;
  });

  return (
    <div className="page">
      <div className="event-filters">
        <SegmentedFilter
          value={timeFilter}
          onChange={setTimeFilter}
          ariaLabel={t("timeFilter.label")}
          options={[
            { value: "upcoming", label: t("timeFilter.upcoming") },
            { value: "past", label: t("timeFilter.past") },
          ]}
        />
        <SegmentedFilter
          value={ownerFilter}
          onChange={setOwnerFilter}
          ariaLabel={t("ownerFilter.label")}
          options={[
            { value: "all", label: t("ownerFilter.all") },
            { value: "mine", label: t("ownerFilter.mine") },
            { value: "others", label: t("ownerFilter.others") },
          ]}
        />
      </div>
      {filteredEvents === undefined ? (
        <p>{t("common.loading")}</p>
      ) : (
        <EventList
          events={filteredEvents}
          emptyMessage={t(timeFilter === "upcoming" ? "upcomingEvents.empty" : "pastEvents.empty")}
        />
      )}
    </div>
  );
}

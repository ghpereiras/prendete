import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { listEventPolls, type EventPoll } from "../api/eventPolls";
import { listEvents, type Event } from "../api/events";
import EventList from "../components/EventList";
import PollList from "../components/PollList";
import SegmentedFilter from "../components/SegmentedFilter";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

type TimeFilterValue = "upcoming" | "past" | "polls";
type OwnerFilterValue = "all" | "mine" | "others";

export default function Events() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [events, setEvents] = useState<Event[] | null>(null);
  const [polls, setPolls] = useState<EventPoll[] | null>(null);
  const [timeFilter, setTimeFilter] = useState<TimeFilterValue>("upcoming");
  const [ownerFilter, setOwnerFilter] = useState<OwnerFilterValue>("all");

  usePageTitle(t("home.greeting", { name: user?.full_name }));

  useEffect(() => {
    listEvents().then(setEvents);
    listEventPolls().then(setPolls);
  }, []);

  function byOwner<T extends { owner_id: number }>(items: T[] | undefined): T[] | undefined {
    return items?.filter((item) => {
      if (ownerFilter === "mine") return item.owner_id === user?.id;
      if (ownerFilter === "others") return item.owner_id !== user?.id;
      return true;
    });
  }

  const now = Date.now();
  const timeFiltered = events?.filter((event) =>
    timeFilter === "upcoming"
      ? new Date(event.starts_at).getTime() >= now
      : new Date(event.starts_at).getTime() < now,
  );
  // Soonest first for upcoming, most recently finished first for past.
  const ordered = timeFilter === "past" ? timeFiltered?.reverse() : timeFiltered;
  const filteredEvents = byOwner(ordered);
  const filteredPolls = byOwner(polls ?? undefined);

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
            { value: "polls", label: t("timeFilter.polls") },
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
      {timeFilter === "polls" ? (
        filteredPolls === undefined ? (
          <p>{t("common.loading")}</p>
        ) : (
          <PollList polls={filteredPolls} emptyMessage={t("pollsFilter.empty")} />
        )
      ) : filteredEvents === undefined ? (
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

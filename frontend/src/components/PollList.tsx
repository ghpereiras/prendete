import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { EventPoll } from "../api/eventPolls";

interface PollListProps {
  polls: EventPoll[];
  emptyMessage: string;
}

export default function PollList({ polls, emptyMessage }: PollListProps) {
  const { t } = useTranslation();

  if (polls.length === 0) {
    return <p>{emptyMessage}</p>;
  }

  return (
    <div className="event-list">
      {polls.map((poll) => (
        <Link key={poll.id} to={`/polls/${poll.id}`} className="event-list-item poll-list-item">
          <div className="event-list-title">
            {poll.title} <span className="poll-badge">{t("home.pollBadge")}</span>
          </div>
          <div className="event-list-meta">
            {t("home.dateOptionsCount", { count: poll.date_options.length })} ·{" "}
            {t("home.organizedBy", { name: poll.owner_name })}
          </div>
        </Link>
      ))}
    </div>
  );
}

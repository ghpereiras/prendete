import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { EventPoll } from "../api/eventPolls";

interface PollListProps {
  polls: EventPoll[];
}

export default function PollList({ polls }: PollListProps) {
  const { t } = useTranslation();

  if (polls.length === 0) {
    return null;
  }

  return (
    <div className="poll-list-section">
      <h2 className="poll-list-heading">{t("home.pendingPolls")}</h2>
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
    </div>
  );
}

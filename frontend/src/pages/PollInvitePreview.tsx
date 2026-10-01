import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { avatarUrl } from "../api/client";
import { previewPollInvite, votePollByInvite, type EventPollInvitePreview } from "../api/eventPolls";
import Avatar from "../components/Avatar";
import EventLocation from "../components/EventLocation";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";
import { formatDateTime } from "../utils/date";

export default function PollInvitePreview() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";
  const { token } = useParams<{ token: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [poll, setPoll] = useState<EventPollInvitePreview | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [selectedOptionIds, setSelectedOptionIds] = useState<number[]>([]);
  const [voteError, setVoteError] = useState<string | null>(null);
  const [voting, setVoting] = useState(false);

  usePageTitle(poll?.title ?? (notFound ? t("pollInvitePreview.notFound") : t("common.loading")));

  useEffect(() => {
    if (!token) return;
    previewPollInvite(token)
      .then(setPoll)
      .catch(() => setNotFound(true));
    // Voter names are only returned to a logged-in viewer, so refetch when that changes.
  }, [token, user?.id]);

  function toggleOption(optionId: number) {
    setSelectedOptionIds((prev) =>
      prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId],
    );
  }

  async function handleVote() {
    if (!token) return;
    setVoteError(null);
    setVoting(true);
    try {
      const voted = await votePollByInvite(token, selectedOptionIds);
      navigate(`/polls/${voted.id}`);
    } catch {
      setVoteError("pollInvitePreview.voteError");
    } finally {
      setVoting(false);
    }
  }

  if (notFound) {
    return (
      <div className="page">
        <p className="error">{t("pollInvitePreview.notFound")}</p>
      </div>
    );
  }

  if (!poll) {
    return <p className="page">{t("common.loading")}</p>;
  }

  const isOwner = user?.id === poll.owner_id;

  return (
    <div className="page">
      {poll.description && <p>{poll.description}</p>}
      <EventLocation
        location={poll.location}
        locationDetails={poll.location_details}
        mapsLink={poll.maps_link}
      />

      {isOwner ? (
        <p>{t("pollInvitePreview.isOwner")}</p>
      ) : (
        <div className="poll-options-list">
          <p>{user ? t("pollInvitePreview.pickDates") : t("pollInvitePreview.proposedDates")}</p>
          {poll.date_options.map((option) =>
            user ? (
              <div key={option.id} className="poll-option-card">
                <label className="poll-option-vote">
                  <input
                    type="checkbox"
                    checked={selectedOptionIds.includes(option.id)}
                    onChange={() => toggleOption(option.id)}
                  />
                  {formatDateTime(option.starts_at, lang)}
                </label>
                {option.voters.length > 0 && (
                  <div className="poll-voters-list">
                    {option.voters.map((voter) => (
                      <span key={voter.user_id} className="poll-voter">
                        <Avatar avatarUrl={avatarUrl(voter.avatar_url)} fullName={voter.full_name} />
                        {voter.full_name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div key={option.id} className="poll-option-card">
                <div className="poll-option-date">{formatDateTime(option.starts_at, lang)}</div>
              </div>
            ),
          )}
          {user ? (
            <>
              {voteError && <p className="error">{t(voteError)}</p>}
              <button onClick={handleVote} disabled={voting}>
                {voting ? t("pollInvitePreview.voting") : t("pollInvitePreview.vote")}
              </button>
            </>
          ) : (
            <div className="invite-auth-prompt">
              <p>{t("pollInvitePreview.needsAuth")}</p>
              <Link className="button-link" to="/login" state={{ from: `/polls/invite/${token}` }}>
                {t("login.title")}
              </Link>
              <Link to="/register" state={{ from: `/polls/invite/${token}` }}>
                {t("login.registerLink")}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

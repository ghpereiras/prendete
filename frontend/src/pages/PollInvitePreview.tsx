import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { avatarUrl, isServerUnavailable, loadWhileServerWakes } from "../api/client";
import { previewPollInvite, votePollByInvite, type EventPollInvitePreview } from "../api/eventPolls";
import Avatar from "../components/Avatar";
import EventLocation from "../components/EventLocation";
import LoadingPage from "../components/LoadingPage";
import GoogleSignInButton from "../components/GoogleSignInButton";
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
  const [unavailable, setUnavailable] = useState(false);
  const [slow, setSlow] = useState(false);
  const [selectedOptionIds, setSelectedOptionIds] = useState<number[]>([]);
  const [voteError, setVoteError] = useState<string | null>(null);
  const [voting, setVoting] = useState(false);

  usePageTitle(poll?.title ?? (notFound || unavailable ? t(unavailable ? "common.serverUnavailable" : "pollInvitePreview.notFound") : t("common.loading")));

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    loadWhileServerWakes(() => previewPollInvite(token), {
      onSlow: () => setSlow(true),
      isCancelled: () => cancelled,
    })
      .then((loaded) => {
        setPoll(loaded);
        // The public link doesn't say which dates the viewer picked, but their name is among the voters.
        setSelectedOptionIds(
          loaded.date_options
            .filter((option) => option.voters.some((voter) => voter.user_id === user?.id))
            .map((option) => option.id),
        );
      })
      .catch((err) => {
        if (cancelled) return;
        if (isServerUnavailable(err)) setUnavailable(true);
        else setNotFound(true);
      });
    return () => {
      cancelled = true;
    };
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

  if (notFound || unavailable) {
    return (
      <div className="page">
        <p className="error">{t(unavailable ? "common.serverUnavailable" : "pollInvitePreview.notFound")}</p>
      </div>
    );
  }

  if (!poll) {
    return <LoadingPage slow={slow} />;
  }

  const isOwner = user?.id === poll.owner_id;

  return (
    <div className="page">
      {poll.description && <p className="multiline-text">{poll.description}</p>}
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
              <div className="form-actions">
                <button type="button" className="primary" onClick={handleVote} disabled={voting}>
                  {voting ? t("pollDetail.savingAvailability") : t("pollDetail.saveAvailability")}
                </button>
              </div>
            </>
          ) : (
            <div className="invite-auth-prompt">
              <p>{t("pollInvitePreview.needsAuth")}</p>
              <GoogleSignInButton returnTo={`/polls/invite/${token}`} />
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

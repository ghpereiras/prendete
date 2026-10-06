import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { avatarUrl, isServerUnavailable, loadWhileServerWakes } from "../api/client";
import {
  deleteEventPoll,
  getEventPoll,
  getPollInviteLink,
  voteEventPoll,
  type EventPoll,
} from "../api/eventPolls";
import Avatar from "../components/Avatar";
import ConfirmModal from "../components/ConfirmModal";
import EventLocation from "../components/EventLocation";
import ExpandableText from "../components/ExpandableText";
import LoadingPage from "../components/LoadingPage";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";
import { formatDateTime } from "../utils/date";

export default function PollDetail() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";
  const { pollId } = useParams<{ pollId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [poll, setPoll] = useState<EventPoll | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [selectedOptionIds, setSelectedOptionIds] = useState<number[]>([]);
  const [savingVotes, setSavingVotes] = useState(false);
  const [voteError, setVoteError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  usePageTitle(poll?.title ?? (error ? t(error) : t("common.loading")));

  useEffect(() => {
    if (!pollId) return;
    let cancelled = false;
    loadWhileServerWakes(() => getEventPoll(Number(pollId)), {
      onSlow: () => setSlow(true),
      isCancelled: () => cancelled,
    })
      .then((loaded) => {
        setPoll(loaded);
        setSelectedOptionIds(
          loaded.date_options.filter((option) => option.voted_by_me).map((option) => option.id),
        );
      })
      .catch((err) => {
        if (!cancelled) setError(isServerUnavailable(err) ? "common.serverUnavailable" : "pollDetail.notFound");
      });
    return () => {
      cancelled = true;
    };
  }, [pollId]);

  const isOwner = user?.id === poll?.owner_id;

  useEffect(() => {
    if (!pollId || !poll || !isOwner) return;
    getPollInviteLink(Number(pollId)).then(({ invite_token }) =>
      setInviteUrl(`${window.location.origin}/polls/invite/${invite_token}`),
    );
  }, [pollId, poll, isOwner]);

  async function copyLink() {
    if (!inviteUrl) return;
    await navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleDelete() {
    if (!poll) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteEventPoll(poll.id);
      navigate("/");
    } catch {
      setDeleteError("pollDetail.deleteError");
      setDeleting(false);
    }
  }

  function toggleOption(optionId: number) {
    setSelectedOptionIds((prev) =>
      prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId],
    );
  }

  async function handleSaveVotes() {
    if (!poll) return;
    setSavingVotes(true);
    setVoteError(null);
    try {
      setPoll(await voteEventPoll(poll.id, selectedOptionIds));
    } catch {
      setVoteError("pollDetail.voteError");
    } finally {
      setSavingVotes(false);
    }
  }

  function chooseSlot(optionId: number) {
    if (!poll) return;
    const option = poll.date_options.find((o) => o.id === optionId);
    if (!option) return;
    navigate("/events/new", {
      state: {
        fromPoll: {
          pollId: poll.id,
          dateOptionId: option.id,
          title: poll.title,
          description: poll.description,
          location: poll.location,
          locationDetails: poll.location_details,
          mapsLink: poll.maps_link,
          durationMinutes: poll.duration_minutes,
          startsAt: option.starts_at,
          voters: option.voters,
        },
      },
    });
  }

  if (error) {
    return (
      <div className="page">
        <p className="error">{t(error)}</p>
      </div>
    );
  }

  if (!poll) {
    return <LoadingPage slow={slow} />;
  }

  return (
    <div className="page">
      {poll.resulting_event_id && (
        <p>
          {t("pollDetail.alreadyResolved")}{" "}
          <Link to={`/events/${poll.resulting_event_id}`}>{t("pollDetail.viewEvent")}</Link>
        </p>
      )}
      {poll.description && <ExpandableText text={poll.description} />}
      <EventLocation
        location={poll.location}
        locationDetails={poll.location_details}
        mapsLink={poll.maps_link}
      />

      {inviteUrl && (
        <div className="invite-link">
          <p>{t("pollDetail.shareLink")}</p>
          <code>{inviteUrl}</code>
          <button onClick={copyLink}>{copied ? t("pollDetail.copied") : t("pollDetail.copy")}</button>
        </div>
      )}

      {!poll.resulting_event_id && (
        <div className="poll-options-list">
          <p>{t("pollDetail.dateOptionsLabel")}</p>
          {poll.date_options.map((option) => (
            <div key={option.id} className="poll-option-card">
              <div className="poll-option-date">{formatDateTime(option.starts_at, lang)}</div>
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
              {isOwner ? (
                <button type="button" onClick={() => chooseSlot(option.id)}>
                  {t("pollDetail.chooseThisSlot")}
                </button>
              ) : (
                <label className="poll-option-vote">
                  <input
                    type="checkbox"
                    checked={selectedOptionIds.includes(option.id)}
                    onChange={() => toggleOption(option.id)}
                  />
                  {t("pollDetail.canAttend")}
                </label>
              )}
            </div>
          ))}
          {!isOwner && (
            <div className="form-actions">
              <button type="button" className="primary" onClick={handleSaveVotes} disabled={savingVotes}>
                {savingVotes ? t("pollDetail.savingAvailability") : t("pollDetail.saveAvailability")}
              </button>
            </div>
          )}
          {voteError && <p className="error">{t(voteError)}</p>}
        </div>
      )}

      {isOwner && (
        <div className="event-actions">
          {!poll.resulting_event_id && (
            <Link to={`/polls/${poll.id}/edit`} className="button-link">
              {t("pollDetail.edit")}
            </Link>
          )}
          <button
            type="button"
            className="button-link danger"
            onClick={() => setConfirmingDelete(true)}
          >
            {t("pollDetail.delete")}
          </button>
        </div>
      )}

      {confirmingDelete && (
        <ConfirmModal
          message={t("pollDetail.confirmDeleteMessage")}
          confirmLabel={deleting ? t("pollDetail.deleting") : t("pollDetail.confirmDelete")}
          cancelLabel={t("pollDetail.cancel")}
          confirming={deleting}
          error={deleteError ? t(deleteError) : null}
          onConfirm={handleDelete}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  );
}

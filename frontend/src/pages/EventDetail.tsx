import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, avatarUrl } from "../api/client";
import {
  deleteEvent,
  endsAt,
  getEvent,
  getInviteLink,
  isRegistrationOpen,
  leaveEvent,
  listAttendees,
  registrationDeadline,
  updateAttendance,
  type Event,
  type EventAttendee,
} from "../api/events";
import Avatar from "../components/Avatar";
import ConfirmModal from "../components/ConfirmModal";
import EventLocation from "../components/EventLocation";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";
import { formatDateTime } from "../utils/date";

export default function EventDetail() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [event, setEvent] = useState<Event | null>(null);
  const [attendees, setAttendees] = useState<EventAttendee[] | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmingLeave, setConfirmingLeave] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [leaveError, setLeaveError] = useState<string | null>(null);
  const [editingComment, setEditingComment] = useState(false);
  const [commentDraft, setCommentDraft] = useState("");
  const [savingComment, setSavingComment] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);

  usePageTitle(event?.title ?? (error ? t(error) : t("common.loading")));

  useEffect(() => {
    if (!eventId) return;
    getEvent(Number(eventId))
      .then(setEvent)
      .catch(() => setError("eventDetail.notFound"));
  }, [eventId]);

  useEffect(() => {
    if (!eventId || !event) return;
    listAttendees(Number(eventId)).then(setAttendees);
  }, [eventId, event]);

  useEffect(() => {
    if (!eventId || !event) return;
    getInviteLink(Number(eventId))
      .then(({ invite_token }) => setInviteUrl(`${window.location.origin}/invite/${invite_token}`))
      .catch((err) => {
        // Non-owners can't fetch the invite link; that's expected, not an error to show.
        if (!(err instanceof ApiError && err.status === 403)) {
          setError("eventDetail.linkError");
        }
      });
  }, [eventId, event]);

  async function copyLink() {
    if (!inviteUrl) return;
    await navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleDelete() {
    if (!event) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteEvent(event.id);
      navigate("/");
    } catch {
      setDeleteError("eventDetail.deleteError");
      setDeleting(false);
    }
  }

  async function handleLeave() {
    if (!event) return;
    setLeaving(true);
    setLeaveError(null);
    try {
      await leaveEvent(event.id);
      navigate("/");
    } catch {
      setLeaveError("eventDetail.leaveError");
      setLeaving(false);
    }
  }

  function startEditingComment(currentComment: string | null) {
    setCommentDraft(currentComment ?? "");
    setCommentError(null);
    setEditingComment(true);
  }

  async function handleSaveComment() {
    if (!event) return;
    setSavingComment(true);
    setCommentError(null);
    try {
      const updated = await updateAttendance(event.id, commentDraft.trim() || null);
      setAttendees((prev) =>
        prev ? prev.map((a) => (a.user_id === user?.id ? { ...a, comment: updated.comment } : a)) : prev,
      );
      setEditingComment(false);
    } catch {
      setCommentError("eventDetail.commentError");
    } finally {
      setSavingComment(false);
    }
  }

  if (error) {
    return (
      <div className="page">
        <p className="error">{t(error)}</p>
      </div>
    );
  }

  if (!event) {
    return <p className="page">{t("common.loading")}</p>;
  }

  const acceptedCount = attendees ? attendees.filter((a) => !a.is_owner).length : null;
  const spotsLeft =
    acceptedCount === null || event.max_attendees === null
      ? null
      : Math.max(event.max_attendees - acceptedCount, 0);
  const isOwner = user?.id === event.owner_id;
  const canManage = isOwner && new Date(event.starts_at).getTime() > Date.now();
  const canLeave = !isOwner;

  return (
    <div className="page">
      {event.description && <p>{event.description}</p>}
      <EventLocation
        location={event.location}
        locationDetails={event.location_details}
        mapsLink={event.maps_link}
      />
      <p>
        {formatDateTime(event.starts_at, lang)} —{" "}
        {formatDateTime(endsAt(event.starts_at, event.duration_minutes), lang)}
      </p>
      <p>
        {event.max_attendees === null
          ? t("eventDetail.unlimitedSpots")
          : spotsLeft === null
            ? t("common.loading")
            : t("eventDetail.spotsLeft", { count: spotsLeft })}
      </p>
      <p className={isRegistrationOpen(event.starts_at, event.registration_deadline_minutes_before) ? undefined : "error"}>
        {isRegistrationOpen(event.starts_at, event.registration_deadline_minutes_before)
          ? t("eventDetail.registrationDeadline", {
              date: formatDateTime(
                registrationDeadline(event.starts_at, event.registration_deadline_minutes_before),
                lang,
              ),
            })
          : t("eventDetail.registrationClosed")}
      </p>

      {inviteUrl && (
        <div className="invite-link">
          <p>{t("eventDetail.shareLink")}</p>
          <code>{inviteUrl}</code>
          <button onClick={copyLink}>
            {copied ? t("eventDetail.copied") : t("eventDetail.copy")}
          </button>
        </div>
      )}

      {attendees && attendees.length > 0 && (
        <div className="attendee-list">
          <p>{t("eventDetail.attendees")}</p>
          <ul>
            {attendees.map((attendee) => {
              const isSelf = !attendee.is_owner && attendee.user_id === user?.id;
              return (
                <li key={attendee.user_id}>
                  <div className="attendee-row">
                    <Avatar avatarUrl={avatarUrl(attendee.avatar_url)} fullName={attendee.full_name} />
                    {attendee.full_name}
                    {attendee.is_owner && (
                      <span className="owner-badge">{t("eventDetail.ownerBadge")}</span>
                    )}
                  </div>
                  {isSelf && editingComment ? (
                    <div className="join-form">
                      <label className="sr-only" htmlFor="attendance-comment">
                        {t("eventDetail.commentLabel")}
                      </label>
                      <textarea
                        id="attendance-comment"
                        value={commentDraft}
                        onChange={(e) => setCommentDraft(e.target.value)}
                        rows={2}
                        maxLength={500}
                      />
                      <div className="form-actions">
                        <button type="button" onClick={() => setEditingComment(false)} disabled={savingComment}>
                          {t("eventDetail.cancel")}
                        </button>
                        <button type="button" onClick={handleSaveComment} disabled={savingComment}>
                          {savingComment ? t("eventDetail.savingComment") : t("eventDetail.saveComment")}
                        </button>
                      </div>
                      {commentError && <p className="error">{t(commentError)}</p>}
                    </div>
                  ) : (
                    <>
                      {attendee.comment && <p className="attendee-comment">"{attendee.comment}"</p>}
                      {isSelf && (
                        <button type="button" onClick={() => startEditingComment(attendee.comment)}>
                          {attendee.comment
                            ? t("eventDetail.editComment")
                            : t("eventDetail.addComment")}
                        </button>
                      )}
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {canManage && (
        <div className="event-actions">
          <Link to={`/events/${event.id}/edit`} className="button-link">
            {t("eventDetail.edit")}
          </Link>
          <button
            type="button"
            className="button-link danger"
            onClick={() => setConfirmingDelete(true)}
          >
            {t("eventDetail.delete")}
          </button>
        </div>
      )}

      {canLeave && (
        <div className="event-actions">
          <button
            type="button"
            className="button-link danger"
            onClick={() => setConfirmingLeave(true)}
          >
            {t("eventDetail.leave")}
          </button>
        </div>
      )}

      {confirmingDelete && (
        <ConfirmModal
          message={t("eventDetail.confirmDeleteMessage")}
          confirmLabel={deleting ? t("eventDetail.deleting") : t("eventDetail.confirmDelete")}
          cancelLabel={t("eventDetail.cancel")}
          confirming={deleting}
          error={deleteError ? t(deleteError) : null}
          onConfirm={handleDelete}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}

      {confirmingLeave && (
        <ConfirmModal
          message={t("eventDetail.confirmLeaveMessage")}
          confirmLabel={leaving ? t("eventDetail.leaving") : t("eventDetail.confirmLeave")}
          cancelLabel={t("eventDetail.cancel")}
          confirming={leaving}
          error={leaveError ? t(leaveError) : null}
          onConfirm={handleLeave}
          onCancel={() => setConfirmingLeave(false)}
        />
      )}
    </div>
  );
}

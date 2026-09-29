import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { avatarUrl } from "../api/client";
import {
  getMyPushSubscription,
  isPushSupported,
  subscribeToPush,
  unsubscribeFromPush,
} from "../api/push";
import Avatar from "../components/Avatar";
import AvatarPicker from "../components/AvatarPicker";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

type AvatarChange = "none" | "removed" | { dataUrl: string };

export default function Profile() {
  const { t } = useTranslation();
  const { user, updateProfile } = useAuth();

  usePageTitle(t("profile.title"));

  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarChange, setAvatarChange] = useState<AvatarChange>("none");
  const [nameError, setNameError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [pushEnabled, setPushEnabled] = useState<boolean | null>(null);
  const [pushError, setPushError] = useState<string | null>(null);
  const [pushSubmitting, setPushSubmitting] = useState(false);

  const pushSupported = isPushSupported();

  useEffect(() => {
    if (!pushSupported) return;
    getMyPushSubscription().then((sub) => setPushEnabled(sub !== null));
  }, [pushSupported]);

  async function handleTogglePush() {
    setPushError(null);
    setPushSubmitting(true);
    try {
      if (pushEnabled) {
        await unsubscribeFromPush();
        setPushEnabled(false);
      } else {
        await subscribeToPush();
        setPushEnabled(true);
      }
    } catch {
      setPushError(
        Notification.permission === "denied"
          ? "profile.pushErrorDenied"
          : "profile.pushErrorGeneric",
      );
    } finally {
      setPushSubmitting(false);
    }
  }

  function startEditing() {
    setFullName(user?.full_name ?? "");
    setAvatarPreview(avatarUrl(user?.avatar_url ?? null));
    setAvatarChange("none");
    setNameError(null);
    setError(null);
    setEditing(true);
  }

  function handleAvatarChange(dataUrl: string | null) {
    setAvatarPreview(dataUrl);
    setAvatarChange(dataUrl ? { dataUrl } : "removed");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!fullName.trim()) {
      setNameError("profile.errorNameRequired");
      return;
    }
    setNameError(null);

    setSubmitting(true);
    try {
      await updateProfile({
        fullName,
        avatarBase64: typeof avatarChange === "object" ? avatarChange.dataUrl : undefined,
        removeAvatar: avatarChange === "removed",
      });
      setEditing(false);
    } catch {
      setError("profile.editError");
    } finally {
      setSubmitting(false);
    }
  }

  if (editing) {
    return (
      <div className="page">
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {error && <p className="error">{t(error)}</p>}
          <AvatarPicker value={avatarPreview} onChange={handleAvatarChange} />
          <label>
            {t("profile.name")}
            <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            {nameError && <span className="field-error">{t(nameError)}</span>}
          </label>
          <div className="form-actions">
            <button type="button" onClick={() => setEditing(false)} disabled={submitting}>
              {t("profile.cancel")}
            </button>
            <button type="submit" disabled={submitting}>
              {submitting ? t("profile.saving") : t("profile.save")}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="page">
      <Avatar avatarUrl={avatarUrl(user?.avatar_url ?? null)} fullName={user?.full_name ?? ""} large />
      <p>
        {t("profile.name")}: {user?.full_name}
      </p>
      <p>
        {t("profile.email")}: {user?.email}
      </p>
      <button type="button" className="button-link" onClick={startEditing}>
        {t("profile.edit")}
      </button>

      {pushSupported && (
        <div className="push-toggle">
          <button type="button" onClick={handleTogglePush} disabled={pushEnabled === null || pushSubmitting}>
            {pushSubmitting
              ? t("profile.pushSaving")
              : pushEnabled
                ? t("profile.pushDisable")
                : t("profile.pushEnable")}
          </button>
          {pushError && <p className="error">{t(pushError)}</p>}
        </div>
      )}
    </div>
  );
}

import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { changePassword, deleteAccount } from "../api/auth";
import { ApiError, avatarUrl } from "../api/client";
import {
  getMyPushSubscription,
  isPushSupported,
  subscribeToPush,
  unsubscribeFromPush,
} from "../api/push";
import Avatar from "../components/Avatar";
import AvatarPicker from "../components/AvatarPicker";
import ConfirmModal from "../components/ConfirmModal";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

const MIN_PASSWORD_LENGTH = 8;

type AvatarChange = "none" | "removed" | { dataUrl: string };

export default function Profile() {
  const { t } = useTranslation();
  const { user, updateProfile, logout } = useAuth();

  const navigate = useNavigate();

  usePageTitle(t("profile.title"));

  const [editing, setEditing] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarChange, setAvatarChange] = useState<AvatarChange>("none");
  const [nameError, setNameError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [pushEnabled, setPushEnabled] = useState<boolean | null>(null);
  const [pushError, setPushError] = useState<string | null>(null);
  const [pushSubmitting, setPushSubmitting] = useState(false);

  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordFieldError, setPasswordFieldError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);

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

  async function handleDeleteAccount() {
    setDeleteError(null);
    setDeleting(true);
    try {
      await deleteAccount();
      logout();
      navigate("/login", { replace: true });
    } catch {
      setDeleteError("profile.deleteAccountError");
      setDeleting(false);
    }
  }

  function startChangingPassword() {
    setCurrentPassword("");
    setNewPassword("");
    setPasswordFieldError(null);
    setPasswordError(null);
    setChangingPassword(true);
  }

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);

    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      setPasswordFieldError("register.errorPasswordTooShort");
      return;
    }
    setPasswordFieldError(null);

    setPasswordSubmitting(true);
    try {
      await changePassword(currentPassword, newPassword);
      setChangingPassword(false);
    } catch (err) {
      setPasswordError(
        err instanceof ApiError && err.status === 400
          ? "profile.changePasswordErrorWrongCurrent"
          : "profile.changePasswordError",
      );
    } finally {
      setPasswordSubmitting(false);
    }
  }

  function startEditing() {
    setFirstName(user?.first_name ?? "");
    setLastName(user?.last_name ?? "");
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

    if (!firstName.trim() || !lastName.trim()) {
      setNameError("profile.errorNameRequired");
      return;
    }
    setNameError(null);

    setSubmitting(true);
    try {
      await updateProfile({
        firstName,
        lastName,
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
            {t("profile.firstName")}
            <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </label>
          <label>
            {t("profile.lastName")}
            <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </label>
          {nameError && <span className="field-error">{t(nameError)}</span>}
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

  if (changingPassword) {
    return (
      <div className="page">
        <form className="auth-form" onSubmit={handleChangePassword} noValidate>
          {passwordError && <p className="error">{t(passwordError)}</p>}
          <label>
            {t("profile.currentPassword")}
            <PasswordInput
              value={currentPassword}
              onChange={setCurrentPassword}
              autoComplete="current-password"
            />
          </label>
          <label>
            {t("profile.newPassword")}
            <PasswordInput value={newPassword} onChange={setNewPassword} autoComplete="new-password" />
            {passwordFieldError && <span className="field-error">{t(passwordFieldError)}</span>}
          </label>
          <div className="form-actions">
            <button type="button" onClick={() => setChangingPassword(false)} disabled={passwordSubmitting}>
              {t("profile.cancel")}
            </button>
            <button type="submit" disabled={passwordSubmitting}>
              {passwordSubmitting ? t("profile.saving") : t("profile.save")}
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
      {user?.has_password && (
        <button type="button" className="button-link" onClick={startChangingPassword}>
          {t("profile.changePassword")}
        </button>
      )}

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

      <button type="button" className="button-link danger" onClick={() => setConfirmingDelete(true)}>
        {t("profile.deleteAccount")}
      </button>

      {confirmingDelete && (
        <ConfirmModal
          message={t("profile.deleteAccountConfirm")}
          confirmLabel={deleting ? t("profile.deleteAccountDeleting") : t("profile.deleteAccountYes")}
          cancelLabel={t("profile.cancel")}
          confirming={deleting}
          error={deleteError ? t(deleteError) : null}
          onConfirm={handleDeleteAccount}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </div>
  );
}

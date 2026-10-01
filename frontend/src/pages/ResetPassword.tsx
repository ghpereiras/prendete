import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { confirmPasswordReset } from "../api/auth";
import AuthTopBar from "../components/AuthTopBar";
import PasswordInput from "../components/PasswordInput";
import { usePageTitle } from "../context/PageTitleContext";

const MIN_PASSWORD_LENGTH = 8;

interface FieldErrors {
  password?: string;
}

export default function ResetPassword() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  usePageTitle(t("resetPassword.title"));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setFieldErrors({ password: "register.errorPasswordTooShort" });
      return;
    }
    setFieldErrors({});

    if (!token) {
      setError("resetPassword.error");
      return;
    }

    setSubmitting(true);
    try {
      await confirmPasswordReset(token, password);
      navigate("/login");
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError("resetPassword.errorInvalidToken");
      } else {
        setError("resetPassword.error");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthTopBar />
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{t("resetPassword.title")}</h1>
        {error && <p className="error">{t(error)}</p>}
        <label>
          {t("resetPassword.newPassword")}
          <PasswordInput value={password} onChange={setPassword} autoComplete="new-password" />
          {fieldErrors.password && <span className="field-error">{t(fieldErrors.password)}</span>}
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? t("resetPassword.submitting") : t("resetPassword.submit")}
        </button>
        <p>
          <Link to="/login">{t("forgotPassword.backToLogin")}</Link>
        </p>
      </form>
    </div>
  );
}

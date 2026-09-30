import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { resendVerification } from "../api/auth";
import { ApiError } from "../api/client";
import AuthTopBar from "../components/AuthTopBar";
import { useAuth } from "../context/AuthContext";

interface FieldErrors {
  email?: string;
  password?: string;
}

export default function Login() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [notVerified, setNotVerified] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [slowServer, setSlowServer] = useState(false);

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!email.trim()) errors.email = "login.errorEmailRequired";
    if (!password) errors.password = "login.errorPasswordRequired";
    return errors;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotVerified(false);
    setResent(false);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSubmitting(true);
    setSlowServer(false);
    const slowServerTimeout = setTimeout(() => setSlowServer(true), 4000);
    try {
      await login(email, password);
      navigate(from);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403 && err.message === "email_not_verified") {
        setNotVerified(true);
      } else {
        setError("login.error");
      }
    } finally {
      clearTimeout(slowServerTimeout);
      setSlowServer(false);
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResending(true);
    try {
      await resendVerification(email);
      setResent(true);
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthTopBar />
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{t("login.title")}</h1>
        {error && <p className="error">{t(error)}</p>}
        {notVerified && (
          <div className="error">
            <p>{t("login.errorNotVerified")}</p>
            {resent ? (
              <p className="hint">{t("login.verificationResent")}</p>
            ) : (
              <button type="button" onClick={handleResend} disabled={resending}>
                {resending ? t("login.resending") : t("login.resendVerification")}
              </button>
            )}
          </div>
        )}
        <label>
          {t("login.email")}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          {fieldErrors.email && <span className="field-error">{t(fieldErrors.email)}</span>}
        </label>
        <label>
          {t("login.password")}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {fieldErrors.password && <span className="field-error">{t(fieldErrors.password)}</span>}
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? t("login.submitting") : t("login.submit")}
        </button>
        {slowServer && <p className="hint">{t("login.slowServer")}</p>}
        <p>
          <Link to="/forgot-password">{t("login.forgotPasswordLink")}</Link>
        </p>
        <p>
          {t("login.noAccount")}{" "}
          <Link to="/register" state={from !== "/" ? { from } : undefined}>
            {t("login.registerLink")}
          </Link>
        </p>
      </form>
    </div>
  );
}

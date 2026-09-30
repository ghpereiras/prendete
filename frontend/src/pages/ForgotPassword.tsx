import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../api/auth";
import AuthTopBar from "../components/AuthTopBar";
import { usePageTitle } from "../context/PageTitleContext";
import type { Language } from "../i18n";

interface FieldErrors {
  email?: string;
}

export default function ForgotPassword() {
  const { t, i18n } = useTranslation();
  const [email, setEmail] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  usePageTitle(t("forgotPassword.title"));

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (!email.trim()) {
      setFieldErrors({ email: "forgotPassword.errorEmailRequired" });
      return;
    }
    setFieldErrors({});

    setSubmitting(true);
    try {
      await requestPasswordReset(email, i18n.resolvedLanguage as Language);
    } finally {
      // Always show the same success message, whether or not the email is
      // registered — the backend never leaks that either.
      setSubmitting(false);
      setSubmitted(true);
    }
  }

  return (
    <div className="auth-page">
      <AuthTopBar />
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{t("forgotPassword.title")}</h1>
        {submitted ? (
          <p>{t("forgotPassword.success")}</p>
        ) : (
          <>
            <p>{t("forgotPassword.instructions")}</p>
            <label>
              {t("login.email")}
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              {fieldErrors.email && <span className="field-error">{t(fieldErrors.email)}</span>}
            </label>
            <button type="submit" disabled={submitting}>
              {submitting ? t("forgotPassword.submitting") : t("forgotPassword.submit")}
            </button>
          </>
        )}
        <p>
          <Link to="/login">{t("forgotPassword.backToLogin")}</Link>
        </p>
      </form>
    </div>
  );
}

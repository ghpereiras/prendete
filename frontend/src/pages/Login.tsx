import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
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
  const [submitting, setSubmitting] = useState(false);

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!email.trim()) errors.email = "login.errorEmailRequired";
    if (!password) errors.password = "login.errorPasswordRequired";
    return errors;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from);
    } catch {
      setError("login.error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthTopBar />
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{t("login.title")}</h1>
        {error && <p className="error">{t(error)}</p>}
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

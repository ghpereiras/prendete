import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { register } from "../api/auth";
import AuthTopBar from "../components/AuthTopBar";
import AvatarPicker from "../components/AvatarPicker";
import { useAuth } from "../context/AuthContext";
import type { Language } from "../i18n";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;

interface FieldErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
}

export default function Register() {
  const { t, i18n } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [avatar, setAvatar] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validate(): FieldErrors {
    const errors: FieldErrors = {};
    if (!firstName.trim()) errors.firstName = "register.errorFirstNameRequired";
    if (!lastName.trim()) errors.lastName = "register.errorLastNameRequired";
    if (!email.trim()) {
      errors.email = "register.errorEmailRequired";
    } else if (!EMAIL_RE.test(email.trim())) {
      errors.email = "register.errorEmailInvalid";
    }
    if (!password) {
      errors.password = "register.errorPasswordRequired";
    } else if (password.length < MIN_PASSWORD_LENGTH) {
      errors.password = "register.errorPasswordTooShort";
    }
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
      await register(email, firstName, lastName, password, (i18n.resolvedLanguage as Language) ?? "es", avatar);
      await login(email, password);
      navigate(from);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("register.errorEmailTaken");
      } else {
        setError("register.errorGeneric");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <AuthTopBar />
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <h1>{t("register.title")}</h1>
        {error && <p className="error">{t(error)}</p>}
        <AvatarPicker value={avatar} onChange={setAvatar} />
        <label>
          {t("register.email")}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          {fieldErrors.email && <span className="field-error">{t(fieldErrors.email)}</span>}
        </label>
        <label>
          {t("register.firstName")}
          <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          {fieldErrors.firstName && <span className="field-error">{t(fieldErrors.firstName)}</span>}
        </label>
        <label>
          {t("register.lastName")}
          <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          {fieldErrors.lastName && <span className="field-error">{t(fieldErrors.lastName)}</span>}
        </label>
        <label>
          {t("register.password")}
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {fieldErrors.password && <span className="field-error">{t(fieldErrors.password)}</span>}
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? t("register.submitting") : t("register.submit")}
        </button>
        <p>
          {t("register.haveAccount")}{" "}
          <Link to="/login" state={from !== "/" ? { from } : undefined}>
            {t("register.loginLink")}
          </Link>
        </p>
      </form>
    </div>
  );
}

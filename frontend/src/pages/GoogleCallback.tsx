import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { readGoogleCallback } from "../utils/googleAuth";

export default function GoogleCallback() {
  const { t } = useTranslation();
  const { loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);
  // StrictMode runs effects twice in dev, but the pending state is read once.
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const result = readGoogleCallback(window.location.hash);
    if (!result) {
      setFailed(true);
      return;
    }
    loginWithGoogle(result.idToken, result.nonce)
      .then(() => navigate(result.returnTo, { replace: true }))
      .catch(() => setFailed(true));
  }, [loginWithGoogle, navigate]);

  if (failed) {
    return (
      <div className="auth-page">
        <p className="error">{t("google.error")}</p>
        <Link to="/login">{t("login.title")}</Link>
      </div>
    );
  }
  return (
    <div className="auth-page">
      <p>{t("google.signingIn")}</p>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { verifyEmail } from "../api/auth";
import AuthTopBar from "../components/AuthTopBar";
import { usePageTitle } from "../context/PageTitleContext";

type Status = "verifying" | "success" | "error";

export default function VerifyEmail() {
  const { t } = useTranslation();
  const { token } = useParams<{ token: string }>();
  const [status, setStatus] = useState<Status>("verifying");

  usePageTitle(t("verifyEmail.title"));

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <div className="auth-page">
      <AuthTopBar />
      <div className="auth-form">
        <h1>{t("verifyEmail.title")}</h1>
        {status === "verifying" && <p>{t("verifyEmail.verifying")}</p>}
        {status === "success" && (
          <>
            <p>{t("verifyEmail.success")}</p>
            <Link to="/login" className="button-link">
              {t("login.title")}
            </Link>
          </>
        )}
        {status === "error" && <p className="error">{t("verifyEmail.error")}</p>}
      </div>
    </div>
  );
}

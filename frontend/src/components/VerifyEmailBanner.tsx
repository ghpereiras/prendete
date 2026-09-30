import { useState } from "react";
import { useTranslation } from "react-i18next";
import { resendVerification } from "../api/auth";
import { useAuth } from "../context/AuthContext";

const GRACE_DAYS = 7;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

export default function VerifyEmailBanner() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  if (!user || user.email_verified_at) return null;

  const daysSinceSignup = Math.floor((Date.now() - new Date(user.created_at).getTime()) / MS_PER_DAY);
  const daysLeft = Math.max(GRACE_DAYS - daysSinceSignup, 0);

  async function handleResend() {
    setResending(true);
    try {
      await resendVerification(user!.email);
      setResent(true);
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="verify-email-banner">
      <span>
        {resent ? t("verifyEmailBanner.resent") : t("verifyEmailBanner.reminder", { count: daysLeft })}
      </span>
      {!resent && (
        <button type="button" onClick={handleResend} disabled={resending}>
          {resending ? t("login.resending") : t("login.resendVerification")}
        </button>
      )}
    </div>
  );
}

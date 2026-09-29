import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getPushSubscription, isPushSupported, subscribeToPush } from "../api/push";
import { useAuth } from "../context/AuthContext";
import { isIos, isStandalone } from "../utils/platform";

const DISMISSED_KEY = "push_prompt_dismissed";

type PromptState = "hidden" | "ios-install" | "ask";

export default function NotificationPrompt() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [state, setState] = useState<PromptState>("hidden");
  const [enabling, setEnabling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    if (localStorage.getItem(DISMISSED_KEY)) return;
    if (!isPushSupported()) return;
    if (Notification.permission === "denied") return;

    let cancelled = false;
    getPushSubscription().then((subscription) => {
      if (cancelled || subscription) return;
      setState(isIos() && !isStandalone() ? "ios-install" : "ask");
    });
    return () => {
      cancelled = true;
    };
  }, [user]);

  function dismiss(persist: boolean) {
    if (persist) localStorage.setItem(DISMISSED_KEY, "1");
    setState("hidden");
  }

  async function handleEnable() {
    setError(null);
    setEnabling(true);
    try {
      await subscribeToPush();
      setState("hidden");
    } catch {
      setError("notificationPrompt.error");
    } finally {
      setEnabling(false);
    }
  }

  if (state === "hidden") return null;

  return (
    <div
      className="confirm-modal-backdrop"
      onClick={() => {
        if (!enabling) dismiss(state === "ask");
      }}
    >
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        {state === "ios-install" ? (
          <>
            <p>{t("notificationPrompt.iosInstall")}</p>
            <div className="confirm-modal-actions">
              <button type="button" onClick={() => dismiss(false)}>
                {t("notificationPrompt.gotIt")}
              </button>
            </div>
          </>
        ) : (
          <>
            <p>{t("notificationPrompt.ask")}</p>
            {error && <p className="error">{t(error)}</p>}
            <div className="confirm-modal-actions">
              <button type="button" onClick={() => dismiss(true)} disabled={enabling}>
                {t("notificationPrompt.decline")}
              </button>
              <button type="button" onClick={handleEnable} disabled={enabling}>
                {enabling ? t("notificationPrompt.enabling") : t("notificationPrompt.enable")}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

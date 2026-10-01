import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getMyPushSubscription, isPushSupported, subscribeToPush } from "../api/push";
import { useAuth } from "../context/AuthContext";
import { isIos, isStandalone } from "../utils/platform";

const DISMISSED_KEY_PREFIX = "push_prompt_dismissed_";

type PromptState = "hidden" | "ios-install" | "ask";

export default function NotificationPrompt() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [state, setState] = useState<PromptState>("hidden");
  const [enabling, setEnabling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    // Scoped per user id: a device's browser is often shared between app
    // accounts, and one user's dismissal (or subscription) shouldn't hide
    // the prompt for another user who never actually enabled push.
    if (localStorage.getItem(DISMISSED_KEY_PREFIX + user.id)) return;

    // iOS Safari only exposes PushManager to an installed (standalone) home
    // screen app — isPushSupported() is correctly false in a regular tab, but
    // that's exactly the case where we need to show the install instructions,
    // so this has to be checked before (not after) the support check below.
    if (isIos() && !isStandalone()) {
      setState("ios-install");
      return;
    }

    if (!isPushSupported()) return;
    if (Notification.permission === "denied") return;

    let cancelled = false;
    getMyPushSubscription().then((subscription) => {
      if (cancelled || subscription) return;
      setState("ask");
    });
    return () => {
      cancelled = true;
    };
  }, [user]);

  function dismiss(persist: boolean) {
    if (persist && user) localStorage.setItem(DISMISSED_KEY_PREFIX + user.id, "1");
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

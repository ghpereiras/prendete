import { useState, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { draftPlan, type AiDraftState } from "../api/ai";
import { ApiError } from "../api/client";
import { usePageTitle } from "../context/PageTitleContext";

function errorKey(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 503) return "aiPlan.errorUnavailable";
    if (err.status === 429) return err.message === "ai_busy" ? "aiPlan.errorBusy" : "aiPlan.errorLimit";
  }
  return "aiPlan.errorGeneric";
}

export default function CreateWithAi() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const examples = t("aiPlan.examples", { returnObjects: true }) as string[];

  usePageTitle(t("aiPlan.title"));

  async function submit() {
    if (!text.trim() || loading) return;
    setError(null);
    setLoading(true);
    try {
      const draft = await draftPlan(text.trim());
      // Several dates are a poll and one (or none) is an event: the draft goes to the form that fits it.
      const state: AiDraftState = { aiDraft: draft };
      navigate(draft.kind === "poll" ? "/polls/new" : "/events/new", { state });
    } catch (err) {
      setError(errorKey(err));
      setLoading(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends (the text is a sentence or two); Shift+Enter still makes a new line.
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void submit();
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-form ai-screen">
        <p className="ai-intro">{t("aiPlan.intro")}</p>
        <label>
          <span className="sr-only">{t("aiPlan.title")}</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("aiPlan.placeholder")}
            rows={4}
            maxLength={600}
            disabled={loading}
            autoFocus
          />
        </label>
        <div className="ai-examples">
          <span>{t("aiPlan.examplesLabel")}</span>
          {examples.map((example) => (
            <button key={example} type="button" onClick={() => setText(example)} disabled={loading}>
              {example}
            </button>
          ))}
        </div>
        <button type="button" onClick={() => void submit()} disabled={loading || !text.trim()}>
          {loading ? t("aiPlan.submitting") : t("aiPlan.submit")}
        </button>
        {error && <p className="error">{t(error)}</p>}
        <p className="hint">{t("aiPlan.footnote")}</p>
      </div>
    </div>
  );
}

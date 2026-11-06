import { useTranslation } from "react-i18next";
import type { PlanDraft } from "../api/ai";

// Shown on the create forms after a draft from the "Create with AI" screen: it is a suggestion, it says why the
// draft became an event or a poll, and it calls out anything the model was unsure about.
export default function AiDraftNotice({ draft }: { draft: PlanDraft }) {
  const { t } = useTranslation();
  // With no date at all there is nothing to explain: the "no_dates" warning says it.
  const why =
    draft.kind === "poll" ? "aiPlan.becamePoll" : draft.dates.length === 1 ? "aiPlan.becameEvent" : null;
  return (
    <div className="ai-notice" role="status">
      <p>{t("aiPlan.reviewNotice")}</p>
      {why && <p>{t(why)}</p>}
      {draft.warnings.length > 0 && (
        <ul>
          {draft.warnings.map((w) => (
            <li key={w}>{t(`aiPlan.warnings.${w}`)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function CreateEventButton() {
  const { t } = useTranslation();
  const { user } = useAuth();

  if (!user) return null;

  return (
    <Link
      to="/events/new"
      className="icon-menu-trigger create-event-button"
      title={t("createEvent.title")}
      aria-label={t("createEvent.title")}
    >
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5z" />
      </svg>
    </Link>
  );
}

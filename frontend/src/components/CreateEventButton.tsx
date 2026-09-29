import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTopBarMenu } from "../context/TopBarMenuContext";

export default function CreateEventButton() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { open, containerRef, handleMouseEnter, handleMouseLeave, close, toggle } =
    useTopBarMenu("create");

  if (!user) return null;

  function goTo(path: string) {
    close();
    navigate(path);
  }

  return (
    <div
      className="icon-menu create-menu"
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        type="button"
        className="icon-menu-trigger create-event-button"
        onClick={toggle}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("createEvent.title")}
      >
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5z" />
        </svg>
      </button>
      {open && (
        <div className="icon-menu-dropdown" role="menu">
          <button type="button" role="menuitem" onClick={() => goTo("/events/new")}>
            {t("createEvent.title")}
          </button>
          <button type="button" role="menuitem" onClick={() => goTo("/polls/new")}>
            {t("createPoll.title")}
          </button>
        </div>
      )}
    </div>
  );
}

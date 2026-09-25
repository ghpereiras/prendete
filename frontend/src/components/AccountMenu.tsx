import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { avatarUrl } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useTopBarMenu } from "../context/TopBarMenuContext";

export default function AccountMenu() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { open, containerRef, handleMouseEnter, handleMouseLeave, close, toggle } =
    useTopBarMenu("account");

  if (!user) return null;

  const initial = user.full_name.trim().charAt(0).toUpperCase();
  const photoUrl = avatarUrl(user.avatar_url);

  function goToProfile() {
    close();
    navigate("/profile");
  }

  function handleLogout() {
    close();
    logout();
  }

  return (
    <div
      className="icon-menu account-menu"
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        type="button"
        className="icon-menu-trigger account-menu-trigger"
        onClick={toggle}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("account.label")}
      >
        {photoUrl ? <img src={photoUrl} alt="" /> : initial}
      </button>
      {open && (
        <div className="icon-menu-dropdown" role="menu">
          <button type="button" role="menuitem" onClick={goToProfile}>
            {t("account.profile")}
          </button>
          <button type="button" role="menuitem" onClick={handleLogout}>
            {t("account.logout")}
          </button>
        </div>
      )}
    </div>
  );
}

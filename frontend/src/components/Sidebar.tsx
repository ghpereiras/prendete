import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

function linkClass({ isActive }: { isActive: boolean }): string {
  return isActive ? "sidebar-link sidebar-link-active" : "sidebar-link";
}

export default function Sidebar() {
  const { t } = useTranslation();

  return (
    <nav className="sidebar">
      <NavLink to="/events/upcoming" className={linkClass}>
        {t("sidebar.upcoming")}
      </NavLink>
      <NavLink to="/events/past" className={linkClass}>
        {t("sidebar.past")}
      </NavLink>
    </nav>
  );
}

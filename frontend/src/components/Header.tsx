import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import AccountMenu from "./AccountMenu";
import CreateEventButton from "./CreateEventButton";
import LanguageSwitcher from "./LanguageSwitcher";
import { usePageTitleValue } from "../context/PageTitleContext";
import { TopBarMenuProvider } from "../context/TopBarMenuContext";

export default function Header() {
  const { t } = useTranslation();
  const title = usePageTitleValue();

  return (
    <header className="app-header">
      <Link to="/" className="home-button" aria-label={t("header.home")}>
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 3 2 12h3v8h6v-6h2v6h6v-8h3L12 3z" />
        </svg>
      </Link>
      <h1 className="app-header-title">{title}</h1>
      <div className="top-bar">
        <TopBarMenuProvider>
          <CreateEventButton />
          <LanguageSwitcher />
          <AccountMenu />
        </TopBarMenuProvider>
      </div>
    </header>
  );
}

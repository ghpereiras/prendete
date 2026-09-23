import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  return (
    <div className="page">
      <h1>{t("home.greeting", { name: user?.full_name })}</h1>
      <p>{user?.email}</p>
      <button onClick={logout}>{t("home.logout")}</button>
    </div>
  );
}

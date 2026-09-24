import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { t } = useTranslation();
  const { user } = useAuth();

  return (
    <div className="page">
      <h1>{t("profile.title")}</h1>
      <p>
        {t("profile.name")}: {user?.full_name}
      </p>
      <p>
        {t("profile.email")}: {user?.email}
      </p>
    </div>
  );
}

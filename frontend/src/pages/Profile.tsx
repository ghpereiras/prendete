import { useTranslation } from "react-i18next";
import { avatarUrl } from "../api/client";
import Avatar from "../components/Avatar";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

export default function Profile() {
  const { t } = useTranslation();
  const { user } = useAuth();

  usePageTitle(t("profile.title"));

  return (
    <div className="page">
      <Avatar avatarUrl={avatarUrl(user?.avatar_url ?? null)} fullName={user?.full_name ?? ""} large />
      <p>
        {t("profile.name")}: {user?.full_name}
      </p>
      <p>
        {t("profile.email")}: {user?.email}
      </p>
    </div>
  );
}

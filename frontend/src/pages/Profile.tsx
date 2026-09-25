import { useTranslation } from "react-i18next";
import { avatarUrl } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";

export default function Profile() {
  const { t } = useTranslation();
  const { user } = useAuth();

  usePageTitle(t("profile.title"));

  const photoUrl = user ? avatarUrl(user) : null;
  const initial = user?.full_name.trim().charAt(0).toUpperCase();

  return (
    <div className="page">
      <div className="profile-avatar">{photoUrl ? <img src={photoUrl} alt="" /> : initial}</div>
      <p>
        {t("profile.name")}: {user?.full_name}
      </p>
      <p>
        {t("profile.email")}: {user?.email}
      </p>
    </div>
  );
}

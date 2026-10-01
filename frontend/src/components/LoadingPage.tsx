import { useTranslation } from "react-i18next";

export default function LoadingPage({ slow }: { slow: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="page">
      <p>{t("common.loading")}</p>
      {slow && <p className="hint">{t("common.slowServer")}</p>}
    </div>
  );
}

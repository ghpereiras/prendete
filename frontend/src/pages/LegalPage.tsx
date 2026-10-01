import { useTranslation } from "react-i18next";
import { usePageTitle } from "../context/PageTitleContext";

interface Section {
  heading: string;
  body: string[];
}

export default function LegalPage({ namespace }: { namespace: "privacy" | "terms" }) {
  const { t } = useTranslation();
  const sections = t(`${namespace}.sections`, { returnObjects: true }) as Section[];

  usePageTitle(t(`${namespace}.title`));

  return (
    <div className="page legal-page">
      <p className="hint">{t(`${namespace}.updated`)}</p>
      {sections.map((section) => (
        <section key={section.heading}>
          <h2>{section.heading}</h2>
          {section.body.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </section>
      ))}
    </div>
  );
}

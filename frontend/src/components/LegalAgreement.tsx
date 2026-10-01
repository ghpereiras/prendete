import { Trans } from "react-i18next";
import { Link } from "react-router-dom";

export default function LegalAgreement() {
  return (
    <p className="hint">
      <Trans
        i18nKey="legal.agree"
        components={{ terms: <Link to="/terms" />, privacy: <Link to="/privacy" /> }}
      />
    </p>
  );
}

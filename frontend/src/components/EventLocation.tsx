import { useTranslation } from "react-i18next";
import { isEmbeddableMapsLink } from "../utils/maps";

interface EventLocationProps {
  location: string | null;
  locationDetails: string | null;
  mapsLink: string | null;
}

export default function EventLocation({ location, locationDetails, mapsLink }: EventLocationProps) {
  const { t } = useTranslation();

  if (!location && !locationDetails && !mapsLink) {
    return null;
  }

  const embeddable = mapsLink && isEmbeddableMapsLink(mapsLink);

  return (
    <div className="event-location">
      {location && <p>{location}</p>}
      {locationDetails && <p className="location-details">{locationDetails}</p>}
      {embeddable && (
        <iframe
          className="maps-embed"
          src={mapsLink}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          title={t("eventDetail.mapTitle")}
        />
      )}
      {mapsLink && !embeddable && (
        <a className="button-link" href={mapsLink} target="_blank" rel="noreferrer">
          {t("eventDetail.viewOnMaps")}
        </a>
      )}
    </div>
  );
}

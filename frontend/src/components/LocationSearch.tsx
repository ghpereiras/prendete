import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { buildEmbedUrl, loadGoogleMaps } from "../utils/googleMaps";

interface LocationSearchResult {
  name: string;
  mapsLink: string;
}

interface LocationSearchProps {
  value: string;
  onQueryChange: (value: string) => void;
  onSelect: (result: LocationSearchResult) => void;
}

const DEBOUNCE_MS = 1000;
const ADDRESS_TYPES = new Set(["street_address", "route", "premise", "subpremise"]);

export default function LocationSearch({ value, onQueryChange, onSelect }: LocationSearchProps) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"loading" | "ready" | "unavailable">("loading");
  const [suggestions, setSuggestions] = useState<google.maps.places.AutocompleteSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sessionTokenRef = useRef<google.maps.places.AutocompleteSessionToken | null>(null);
  const debounceRef = useRef<number | null>(null);

  useEffect(() => {
    loadGoogleMaps()
      .then(() => setStatus("ready"))
      .catch(() => setStatus("unavailable"));
  }, []);

  function newSessionToken(): google.maps.places.AutocompleteSessionToken {
    const token = new google.maps.places.AutocompleteSessionToken();
    sessionTokenRef.current = token;
    return token;
  }

  function handleQueryChange(nextValue: string) {
    onQueryChange(nextValue);
    setError(null);

    if (debounceRef.current !== null) {
      window.clearTimeout(debounceRef.current);
    }
    if (!nextValue.trim()) {
      setSuggestions([]);
      return;
    }

    debounceRef.current = window.setTimeout(async () => {
      setSearching(true);
      try {
        const { AutocompleteSuggestion } = (await google.maps.importLibrary(
          "places",
        )) as google.maps.PlacesLibrary;
        const sessionToken = sessionTokenRef.current ?? newSessionToken();
        const { suggestions: results } = await AutocompleteSuggestion.fetchAutocompleteSuggestions({
          input: nextValue,
          sessionToken,
        });
        setSuggestions(results);
      } catch {
        setError("createEvent.locationSearchError");
      } finally {
        setSearching(false);
      }
    }, DEBOUNCE_MS);
  }

  async function handleSelect(suggestion: google.maps.places.AutocompleteSuggestion) {
    const prediction = suggestion.placePrediction;
    if (!prediction) return;

    setSuggestions([]);
    onQueryChange(prediction.text.text);
    setSearching(true);
    try {
      const { place } = await prediction.toPlace().fetchFields({
        fields: ["id", "displayName", "formattedAddress", "location", "types"],
      });
      const isAddress = place.types?.some((type) => ADDRESS_TYPES.has(type)) ?? false;
      const name = isAddress
        ? place.formattedAddress ?? prediction.text.text
        : place.displayName ?? place.formattedAddress ?? prediction.text.text;
      onSelect({
        name,
        mapsLink: buildEmbedUrl(place.id),
      });
    } catch {
      setError("createEvent.locationSearchError");
    } finally {
      setSearching(false);
      sessionTokenRef.current = null; // sessions end once a place is fetched
    }
  }

  return (
    <label className="location-search">
      {t("createEvent.location")}
      <input
        type="text"
        value={value}
        onChange={(e) => handleQueryChange(e.target.value)}
        placeholder={t("createEvent.locationSearchPlaceholder")}
        autoComplete="off"
        disabled={status !== "ready"}
      />
      {status === "unavailable" && (
        <span className="field-error">{t("createEvent.locationSearchUnavailable")}</span>
      )}
      {error && <span className="field-error">{t(error)}</span>}
      {suggestions.length > 0 && (
        <ul className="location-search-suggestions">
          {suggestions.map((suggestion, index) => (
            <li key={suggestion.placePrediction?.placeId ?? index}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => handleSelect(suggestion)}
              >
                {suggestion.placePrediction?.text.text}
              </button>
            </li>
          ))}
        </ul>
      )}
      {searching && <span className="field-hint">{t("common.loading")}</span>}
    </label>
  );
}

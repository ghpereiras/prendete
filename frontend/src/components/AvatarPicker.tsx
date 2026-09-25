import { useRef, useState, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import Cropper, { type Area, type Point } from "react-easy-crop";
import { cropImageToDataUrl } from "../utils/image";

const OUTPUT_SIZE = 256;
const MAX_FILE_BYTES = 8 * 1024 * 1024;

interface AvatarPickerProps {
  value: string | null;
  onChange: (dataUrl: string | null) => void;
}

export default function AvatarPicker({ value, onChange }: AvatarPickerProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [rawImageSrc, setRawImageSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [error, setError] = useState<string | null>(null);

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function handleFileSelected(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setError(null);
    if (!file.type.startsWith("image/")) {
      setError("avatarPicker.errorInvalidFile");
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setError("avatarPicker.errorTooLarge");
      return;
    }

    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setCroppedAreaPixels(null);
    setRawImageSrc(URL.createObjectURL(file));
  }

  function closeCropper() {
    if (rawImageSrc) URL.revokeObjectURL(rawImageSrc);
    setRawImageSrc(null);
  }

  async function confirmCrop() {
    if (!rawImageSrc || !croppedAreaPixels) return;
    const dataUrl = await cropImageToDataUrl(rawImageSrc, croppedAreaPixels, OUTPUT_SIZE);
    onChange(dataUrl);
    closeCropper();
  }

  function removePhoto() {
    onChange(null);
  }

  return (
    <div className="avatar-picker">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={handleFileSelected}
      />
      <button
        type="button"
        className="avatar-picker-trigger"
        onClick={openFilePicker}
        aria-label={t("avatarPicker.label")}
      >
        {value ? (
          <img src={value} alt="" />
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M9 3 7.17 5H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3.17L15 3H9zm3 15a5 5 0 1 1 0-10 5 5 0 0 1 0 10z" />
          </svg>
        )}
      </button>
      <div className="avatar-picker-actions">
        <button type="button" className="link-button" onClick={openFilePicker}>
          {value ? t("avatarPicker.change") : t("avatarPicker.choose")}
        </button>
        {value && (
          <button type="button" className="link-button" onClick={removePhoto}>
            {t("avatarPicker.remove")}
          </button>
        )}
      </div>
      {error && <span className="field-error">{t(error)}</span>}

      {rawImageSrc && (
        <div className="crop-modal-backdrop">
          <div className="crop-modal">
            <h2>{t("avatarPicker.cropTitle")}</h2>
            <div className="cropper-container">
              <Cropper
                image={rawImageSrc}
                crop={crop}
                zoom={zoom}
                aspect={1}
                cropShape="round"
                showGrid={false}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_, pixels) => setCroppedAreaPixels(pixels)}
              />
            </div>
            <label className="zoom-slider">
              <span className="sr-only">{t("avatarPicker.zoom")}</span>
              <input
                type="range"
                min={1}
                max={3}
                step={0.1}
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
              />
            </label>
            <div className="crop-modal-actions">
              <button type="button" onClick={closeCropper}>
                {t("avatarPicker.cancel")}
              </button>
              <button type="button" onClick={confirmCrop}>
                {t("avatarPicker.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

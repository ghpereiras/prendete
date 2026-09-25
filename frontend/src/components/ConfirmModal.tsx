interface ConfirmModalProps {
  message: string;
  confirmLabel: string;
  cancelLabel: string;
  confirming: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  message,
  confirmLabel,
  cancelLabel,
  confirming,
  error,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <div
      className="confirm-modal-backdrop"
      onClick={() => {
        if (!confirming) onCancel();
      }}
    >
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <p>{message}</p>
        {error && <p className="error">{error}</p>}
        <div className="confirm-modal-actions">
          <button type="button" onClick={onCancel} disabled={confirming}>
            {cancelLabel}
          </button>
          <button type="button" className="danger" onClick={onConfirm} disabled={confirming}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

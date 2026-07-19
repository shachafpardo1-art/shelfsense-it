interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  busy,
  onCancel,
  onConfirm,
}: ConfirmDialogProps): JSX.Element {
  return (
    <div className="overlay" role="presentation">
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
        <div className="modal-header">
          <h2 id="confirm-title">{title}</h2>
        </div>
        <p className="modal-copy">{message}</p>
        <div className="modal-actions">
          <button type="button" className="button button-secondary" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="button button-danger" onClick={onConfirm} disabled={busy}>
            {busy ? "Deleting..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

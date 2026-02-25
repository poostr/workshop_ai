import { useRef, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiClient } from "../shared/api/client";
import { getLocalizedErrorMessage } from "../shared/api/errors";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: (typeId: number) => void;
}

export function CreateTypeModal({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
      inputRef.current?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      setName("");
      setError(null);
      setSubmitting(false);
    }
  }, [open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (e: Event) => {
      e.preventDefault();
      onClose();
    };
    dialog.addEventListener("cancel", handleCancel);
    return () => dialog.removeEventListener("cancel", handleCancel);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setError(null);
    setSubmitting(true);
    try {
      const created = await apiClient.createType({ name: trimmed });
      onCreated(created.id);
    } catch (err) {
      setError(getLocalizedErrorMessage(err, t));
    } finally {
      setSubmitting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="modal-dialog"
      onClick={handleBackdropClick}
    >
      <div className="modal-content">
        <h3>{t("pages.createType.title")}</h3>
        <form
          className="create-form"
          onSubmit={(e) => void handleSubmit(e)}
        >
          <label>
            {t("pages.createType.nameLabel")}
            <input
              ref={inputRef}
              type="text"
              value={name}
              placeholder={t("pages.createType.namePlaceholder")}
              onChange={(e) => setName(e.target.value)}
              maxLength={255}
            />
          </label>

          {error && <p className="error-message">{error}</p>}

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || name.trim().length === 0}
            >
              {t("pages.createType.submit")}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
            >
              {t("pages.createType.cancel")}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}

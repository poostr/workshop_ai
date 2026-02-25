import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiClient, ApiClientError } from "../shared/api/client";

export function CreateTypePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setError(null);
    setSubmitting(true);
    try {
      const created = await apiClient.createType({ name: trimmed });
      navigate(`/types/${created.id}`);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(t(`errors.${err.code}`, { defaultValue: err.message }));
      } else {
        setError(t("errors.ERR_UNKNOWN"));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="page-card">
      <h2>{t("pages.createType.title")}</h2>
      <form
        className="create-form"
        onSubmit={(e) => void handleSubmit(e)}
      >
        <label>
          {t("pages.createType.nameLabel")}
          <input
            type="text"
            value={name}
            placeholder={t("pages.createType.namePlaceholder")}
            onChange={(e) => setName(e.target.value)}
            maxLength={255}
            autoFocus
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
          <Link to="/" className="btn btn-secondary">
            {t("pages.createType.cancel")}
          </Link>
        </div>
      </form>
    </section>
  );
}

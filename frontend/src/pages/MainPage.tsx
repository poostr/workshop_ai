import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiClient } from "../shared/api/client";
import { getLocalizedErrorMessage } from "../shared/api/errors";
import type { TypeListItem } from "../shared/api/types";
import { STAGES } from "../shared/api/types";
import { CreateTypeModal } from "../components/CreateTypeModal";
import { ExportImportSection } from "../components/ExportImportSection";

export function MainPage() {
  const { t } = useTranslation();
  const [types, setTypes] = useState<TypeListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchTypes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listTypes();
      setTypes(data.items);
    } catch (err) {
      setError(getLocalizedErrorMessage(err, t));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void fetchTypes();
  }, [fetchTypes]);

  const handleTypeCreated = () => {
    setModalOpen(false);
    void fetchTypes();
  };

  const filtered = types.filter((item) =>
    item.name.toLowerCase().includes(search.toLowerCase()),
  );

  const totalCount = (item: TypeListItem) =>
    STAGES.reduce(
      (sum, stage) =>
        sum + item.counts[stage.toLowerCase() as keyof typeof item.counts],
      0,
    );

  return (
    <section className="page-main">
      <div className="page-header">
        <h2>{t("pages.main.title")}</h2>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setModalOpen(true)}
        >
          {t("pages.main.addType")}
        </button>
      </div>

      {types.length > 0 && (
        <input
          type="text"
          className="search-input"
          placeholder={t("pages.main.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      )}

      {loading && <div className="loading-placeholder" />}

      {error && <p className="error-message">{error}</p>}

      {!loading && !error && filtered.length === 0 && types.length === 0 && (
        <div className="empty-state">
          <p>{t("pages.main.empty")}</p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setModalOpen(true)}
          >
            {t("pages.main.emptyCta")}
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && types.length > 0 && (
        <p className="empty-search">{t("pages.main.emptySearch")}</p>
      )}

      {!loading && filtered.length > 0 && (
        <ul className="type-list">
          {filtered.map((item) => (
            <li key={item.id} className="type-card">
              <Link to={`/types/${item.id}`} className="type-card-link">
                <span className="type-name">{item.name}</span>
                <span className="type-total">
                  {t("pages.main.total")}: {totalCount(item)}
                </span>
              </Link>
              <div className="type-stages">
                {STAGES.map((stage) => (
                  <span key={stage} className="stage-badge">
                    <span className="stage-label">{t(`stages.${stage}`)}</span>
                    <span className="stage-count">
                      {
                        item.counts[
                          stage.toLowerCase() as keyof typeof item.counts
                        ]
                      }
                    </span>
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      <ExportImportSection onImported={fetchTypes} />

      <CreateTypeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={handleTypeCreated}
      />
    </section>
  );
}

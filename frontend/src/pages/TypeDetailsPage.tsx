import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { apiClient } from "../shared/api/client";
import { getLocalizedErrorMessage } from "../shared/api/errors";
import type {
  TypeListItem,
  TypeHistoryGroup,
  StageCode,
} from "../shared/api/types";
import { STAGES, STAGE_INDEX } from "../shared/api/types";

function StageCountsSection({ item }: { item: TypeListItem }) {
  const { t } = useTranslation();

  return (
    <div className="counts-section">
      <h3>{t("pages.typeDetails.counts")}</h3>
      <div className="counts-grid">
        {STAGES.map((stage) => (
          <div key={stage} className="count-cell">
            <span className="count-label">{t(`stages.${stage}`)}</span>
            <span className="count-value">
              {item.counts[stage.toLowerCase() as keyof typeof item.counts]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MoveSection({
  item,
  onMoved,
}: {
  item: TypeListItem;
  onMoved: () => void;
}) {
  const { t } = useTranslation();
  const [fromStage, setFromStage] = useState<StageCode>("IN_BOX");
  const [toStage, setToStage] = useState<StageCode>("BUILDING");
  const [qty, setQty] = useState(1);
  const [moveError, setMoveError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const stageCount = (s: StageCode): number =>
    item.counts[s.toLowerCase() as keyof typeof item.counts];

  const availableFrom = STAGES.filter(
    (s) => stageCount(s) > 0 && STAGE_INDEX[s] < STAGES.length - 1,
  );

  const availableTo = STAGES.filter(
    (s) => STAGE_INDEX[s] > STAGE_INDEX[fromStage],
  );

  const maxQty = stageCount(fromStage);

  useEffect(() => {
    if (availableFrom.length > 0 && !availableFrom.includes(fromStage)) {
      setFromStage(availableFrom[0]);
    }
  }, [availableFrom, fromStage]);

  useEffect(() => {
    if (availableTo.length > 0 && !availableTo.includes(toStage)) {
      setToStage(availableTo[0]);
    }
  }, [fromStage, availableTo, toStage]);

  useEffect(() => {
    if (qty > maxQty) setQty(Math.max(1, maxQty));
  }, [maxQty, qty]);

  const handleMove = async (e: React.FormEvent) => {
    e.preventDefault();
    setMoveError(null);
    setSubmitting(true);
    try {
      await apiClient.moveType(item.id, {
        from_stage: fromStage,
        to_stage: toStage,
        qty,
      });
      onMoved();
    } catch (err) {
      setMoveError(getLocalizedErrorMessage(err, t));
    } finally {
      setSubmitting(false);
    }
  };

  if (availableFrom.length === 0) {
    return (
      <div className="move-section">
        <h3>{t("pages.typeDetails.move")}</h3>
        <p className="section-empty">{t("pages.typeDetails.moveNoAvailable")}</p>
      </div>
    );
  }

  return (
    <div className="move-section">
      <h3>{t("pages.typeDetails.move")}</h3>
      <form className="move-form" onSubmit={(e) => void handleMove(e)}>
        <label>
          {t("pages.typeDetails.moveFrom")}
          <select
            value={fromStage}
            onChange={(e) => setFromStage(e.target.value as StageCode)}
          >
            {availableFrom.map((s) => (
              <option key={s} value={s}>
                {t(`stages.${s}`)}
              </option>
            ))}
          </select>
        </label>

        <label>
          {t("pages.typeDetails.moveTo")}
          <select
            value={toStage}
            onChange={(e) => setToStage(e.target.value as StageCode)}
          >
            {availableTo.map((s) => (
              <option key={s} value={s}>
                {t(`stages.${s}`)}
              </option>
            ))}
          </select>
        </label>

        <label>
          {t("pages.typeDetails.moveQty")}
          <input
            type="number"
            min={1}
            max={maxQty}
            value={qty}
            onChange={(e) => setQty(Number(e.target.value))}
          />
          <span className="available-hint">
            {t("pages.typeDetails.available", { count: maxQty })}
          </span>
        </label>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || maxQty === 0 || availableTo.length === 0}
        >
          {t("pages.typeDetails.moveSubmit")}
        </button>

        {moveError && <p className="error-message">{moveError}</p>}
      </form>
    </div>
  );
}

function formatHistoryTimestamp(iso: string, locale: string): string {
  const date = new Date(iso);
  const resolvedLocale = locale === "ru" ? "ru-RU" : "en-US";
  return date.toLocaleString(resolvedLocale, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function HistorySection({
  typeId,
  refreshKey,
}: {
  typeId: number;
  refreshKey: number;
}) {
  const { t, i18n } = useTranslation();
  const [groups, setGroups] = useState<TypeHistoryGroup[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getTypeHistory(typeId);
      setGroups(data.items);
    } catch {
      /* history fetch failures are non-critical */
    } finally {
      setLoading(false);
    }
  }, [typeId]);

  useEffect(() => {
    void fetchHistory();
  }, [fetchHistory, refreshKey]);

  const displayGroups = [...groups].reverse();

  return (
    <div className="history-section">
      <h3>{t("pages.typeDetails.history")}</h3>
      {loading && <div className="loading-placeholder" />}
      {!loading && displayGroups.length === 0 && (
        <p className="empty-history">{t("pages.typeDetails.historyEmpty")}</p>
      )}
      {!loading && displayGroups.length > 0 && (
        <ul className="history-list">
          {displayGroups.map((g, idx) => (
            <li key={idx} className="history-item">
              <span className="history-transition">
                {t(`stages.${g.from_stage}`)} → {t(`stages.${g.to_stage}`)}
              </span>
              <span className="history-qty">
                {t("pages.typeDetails.historyQty", { qty: g.qty })}
              </span>
              <time
                className="history-time"
                dateTime={g.timestamp}
              >
                {formatHistoryTimestamp(g.timestamp, i18n.language)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function TypeDetailsPage() {
  const { typeId } = useParams();
  const { t } = useTranslation();
  const [item, setItem] = useState<TypeListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const numericId = typeId ? Number(typeId) : NaN;

  const fetchType = useCallback(async () => {
    if (Number.isNaN(numericId)) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setNotFound(false);
      const data = await apiClient.getType(numericId);
      setItem(data);
    } catch {
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  }, [numericId]);

  useEffect(() => {
    void fetchType();
  }, [fetchType, refreshKey]);

  const handleMoved = () => setRefreshKey((k) => k + 1);

  if (loading) {
    return (
      <section className="page-card">
        <div className="loading-placeholder" />
      </section>
    );
  }

  if (notFound || !item) {
    return (
      <section className="page-card">
        <p>{t("pages.typeDetails.notFound")}</p>
        <Link to="/" className="btn">
          {t("pages.typeDetails.back")}
        </Link>
      </section>
    );
  }

  return (
    <section className="page-details">
      <Link to="/" className="back-link">
        {t("pages.typeDetails.back")}
      </Link>
      <h2>{item.name}</h2>

      <StageCountsSection item={item} />
      <MoveSection item={item} onMoved={handleMoved} />
      <HistorySection typeId={item.id} refreshKey={refreshKey} />
    </section>
  );
}

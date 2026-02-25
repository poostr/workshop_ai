import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiClient } from "../shared/api/client";
import { getLocalizedErrorMessage } from "../shared/api/errors";
import type { ImportRequest } from "../shared/api/types";

interface Props {
  onImported: () => void;
}

function downloadJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function buildExportFilename(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const stamp = [
    now.getFullYear(),
    pad(now.getMonth() + 1),
    pad(now.getDate()),
    pad(now.getHours()),
    pad(now.getMinutes()),
  ].join("");
  return `miniatures-export-${stamp}.json`;
}

export function ExportImportSection({ onImported }: Props) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handleExport = async () => {
    setMessage(null);
    setExporting(true);
    try {
      const data = await apiClient.exportState();
      downloadJson(data, buildExportFilename());
    } catch (err) {
      setMessage({ type: "error", text: getLocalizedErrorMessage(err, t) });
    } finally {
      setExporting(false);
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelected = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = e.target.files?.[0];
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (!file) return;

    setMessage(null);
    setImporting(true);
    try {
      const text = await file.text();
      let parsed: ImportRequest;
      try {
        parsed = JSON.parse(text) as ImportRequest;
      } catch {
        setMessage({
          type: "error",
          text: t("errors.ERR_INVALID_IMPORT_FORMAT"),
        });
        return;
      }
      await apiClient.importState(parsed);
      setMessage({ type: "success", text: t("importExport.importSuccess") });
      onImported();
    } catch (err) {
      setMessage({ type: "error", text: getLocalizedErrorMessage(err, t) });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="export-import-section">
      <div className="export-import-actions">
        <button
          type="button"
          className="btn btn-secondary"
          disabled={exporting}
          onClick={() => void handleExport()}
        >
          {t("importExport.exportBtn")}
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={importing}
          onClick={handleImportClick}
        >
          {t("importExport.importBtn")}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          hidden
          onChange={(e) => void handleFileSelected(e)}
        />
      </div>
      {message && (
        <p
          className={
            message.type === "success" ? "success-message" : "error-message"
          }
        >
          {message.text}
        </p>
      )}
    </div>
  );
}

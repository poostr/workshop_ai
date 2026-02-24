import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

export function TypeDetailsPage() {
  const { typeId } = useParams();
  const { t } = useTranslation();

  return (
    <section className="page-card">
      <h2>{t("pages.typeDetails.title")}</h2>
      <p>{t("pages.typeDetails.placeholder", { id: typeId ?? "-" })}</p>
    </section>
  );
}

import { useTranslation } from "react-i18next";

export function MainPage() {
  const { t } = useTranslation();

  return (
    <section className="page-card">
      <h2>{t("pages.main.title")}</h2>
      <p>{t("pages.main.placeholder")}</p>
    </section>
  );
}

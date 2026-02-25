import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function AppLayout() {
  const { i18n, t } = useTranslation();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="app-logo-link">
          <h1>{t("app.title")}</h1>
        </Link>
        <div
          className="lang-switcher"
          role="group"
          aria-label={t("app.language")}
        >
          <button
            type="button"
            className={i18n.language === "ru" ? "active" : ""}
            onClick={() => void i18n.changeLanguage("ru")}
          >
            RU
          </button>
          <button
            type="button"
            className={i18n.language === "en" ? "active" : ""}
            onClick={() => void i18n.changeLanguage("en")}
          >
            EN
          </button>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

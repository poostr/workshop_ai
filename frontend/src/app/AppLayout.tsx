import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function AppLayout() {
  const { i18n, t } = useTranslation();

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>{t("app.title")}</h1>
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

      <nav className="app-nav">
        <Link to="/">{t("nav.main")}</Link>
        <Link to="/types/demo">{t("nav.typeDetails")}</Link>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

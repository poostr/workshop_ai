# CLEAN-004 — Приборка этапа D + security check

## Статус: Выполнено

## Что сделано

### Удалены неиспользуемые i18n-ключи
- Удалён ключ `nav.main` и вся секция `nav` из словарей `ru.ts` и `en.ts` — ключ не использовался после упрощения навигации в `AppLayout`.
- Удалён ключ `importExport.importError` из обоих словарей — ошибки импорта обрабатываются через `getLocalizedErrorMessage`, а не через отдельный ключ.

### Проверка неиспользуемых компонентов
- Все компоненты (`AppLayout`, `MainPage`, `TypeDetailsPage`, `CreateTypeModal`, `ExportImportSection`) используются и импортируются.
- Устаревшие компоненты (`CreateTypePage`, маршрут `/types/new`) были удалены ранее в FE-004.

### Проверка утечек в консоль
- Frontend: ноль `console.log`, `console.warn`, `console.error`, `console.debug`, `console.info`.
- Backend: ноль `print()` и `logging.*` вызовов.
- Данные экспорта/импорта нигде не логируются.

### Security check
- CORS: явный allowlist (`localhost:8080`, `127.0.0.1:8080`, `localhost`, `127.0.0.1`), `allow_credentials=False`, методы `GET/POST/OPTIONS`.
- Nginx: API проксируется только через `^~ /api/`, `proxy_redirect off`, SPA history fallback.
- Секреты: отсутствуют в коде, используются env-переменные.
- Валидация: `extra="forbid"`, strict-поля, `model_validator` на import.

### Quality gates
- Backend: `ruff check` — 0 ошибок, `pytest` — 25 passed.
- Frontend: `tsc --noEmit` — 0 ошибок, `eslint` — 0 ошибок, `vite build` — dist/ собран.

## ADR
- [ADR-0028](../ADR/ADR-0028-clean-stage-d-i18n-security.md)

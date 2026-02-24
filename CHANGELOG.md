# Changelog

## 2026-02-24

### INIT-001

- Создан базовый каркас репозитория: `backend/`, `frontend/`, `ops/`.
- Добавлены базовые инфраструктурные файлы: `README.md`, `.env.example`, `.gitignore`, `docker-compose.yml`.
- Добавлен стартовый nginx-конфиг: `ops/nginx/default.conf`.
- Добавлены процессные артефакты: `ADR/ADR-0001-repo-scaffold.md`, `tasks/INIT-001.md`.
- В `BACKLOG.md` задача `INIT-001` отмечена как выполненная.

### INIT-002

- Реализован backend bootstrap на FastAPI:
  - `backend/app/main.py` (`create_app`, `GET /health`);
  - `backend/app/config.py` (чтение `APP_ENV`, `LOG_LEVEL`, `DATABASE_URL` из env);
  - `backend/app/api/v1/router.py` (базовый v1-роутер).
- Добавлены backend зависимости и контейнеризация:
  - `backend/pyproject.toml`;
  - `backend/Dockerfile`.
- Обновлён `docker-compose.yml`:
  - app сервис теперь собирается из `backend/Dockerfile` и поднимает API на `8000`;
  - добавлен healthcheck app;
  - убран проброс `5432:5432` у postgres для устранения локального порт-конфликта.
- Добавлены тесты backend:
  - `backend/tests/test_app.py`;
  - `backend/tests/conftest.py`.
- В `BACKLOG.md` задача `INIT-002` отмечена как выполненная.
- Добавлены артефакты процесса:
  - `ADR/ADR-0002-backend-bootstrap-init-002.md`;
  - `tasks/INIT-002.md`.

### INIT-003

- Выполнен bootstrap frontend на `React + TypeScript + Vite`.
- Добавлена минимальная структура frontend-приложения:
  - роутинг (`/` и `/types/:typeId`) с заглушками страниц `Main` и `TypeDetails`;
  - базовый layout с переключателем языка RU/EN;
  - каркас i18n (`react-i18next`) со словарями `ru/en`;
  - каркас API-клиента (`src/shared/api/client.ts`) и типизация ошибок API.
- Добавлены frontend-конфиги и npm-скрипты (`dev`, `build`, `preview`).
- Подтверждена сборка `frontend` в `dist/`.
- В `BACKLOG.md` задача `INIT-003` отмечена как выполненная.
- В `BACKLOG.md` добавлена новая задача `INIT-006` (отдельный quality gate для frontend typecheck).
- Добавлены артефакты процесса:
  - `ADR/ADR-0003-frontend-bootstrap-init-003.md`;
  - `tasks/INIT-003.md`.

### INIT-004

- Обновлён `docker-compose.yml` до целевой связки `app + postgres + nginx` с корректными зависимостями готовности:
  - добавлен `healthcheck` для `postgres`;
  - `app` запускается после готовности БД (`service_healthy`).
- Реализован автопрогон миграций при старте backend:
  - добавлены `backend/alembic.ini`, `backend/alembic/env.py`, стартовая ревизия `backend/alembic/versions/0001_init_schema_placeholder.py`;
  - запуск `app` переведён на `backend/entrypoint.sh` (`alembic upgrade head` перед `uvicorn`).
- `nginx` переведён на сборку собственного образа:
  - добавлен `ops/nginx/Dockerfile` (multi-stage сборка frontend и копирование `dist` в nginx image);
  - в compose убраны runtime bind mounts frontend-каталога.
- Добавлен `.dockerignore` для сокращения контекста сборки.
- В `BACKLOG.md` задача `INIT-004` отмечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0004-docker-compose-init-004.md`;
  - `tasks/INIT-004.md`.


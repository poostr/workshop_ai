# Changelog

## 2026-02-25

### DB-003

- Добавлена Alembic-миграция `backend/alembic/versions/0002_seed_stage_counts_on_type_insert.py`, которая гарантирует авто-сидирование `stage_counts` при создании записи в `miniature_types`.
- Реализован dialect-aware подход в миграции:
  - для PostgreSQL: функция-триггер `seed_stage_counts_for_new_type()` и триггер `trg_seed_stage_counts_after_type_insert`;
  - для SQLite (тестовый контур): `AFTER INSERT` trigger с эквивалентной логикой.
- Расширен интеграционный тест `backend/tests/test_migrations.py`:
  - добавлена проверка, что после вставки нового типа автоматически появляются записи по всем 5 стадиям (`IN_BOX`, `BUILDING`, `PRIMING`, `PAINTING`, `DONE`) со значением `0`.
- В `BACKLOG.md` задача `DB-003` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0010-stage-counts-seeding-db-003.md`;
  - `tasks/DB-003.md`.

### DB-002

- Подтверждён bootstrap Alembic в backend: используются `backend/alembic.ini`, `backend/alembic/env.py` и стартовая ревизия `backend/alembic/versions/0001_init_schema_placeholder.py`.
- Зафиксирован автопрогон миграций при старте контейнера через `backend/entrypoint.sh` (`alembic upgrade head` перед запуском `uvicorn`).
- Добавлен интеграционный тест `backend/tests/test_migrations.py`:
  - выполняет `alembic upgrade head` на временной БД;
  - проверяет создание таблиц `miniature_types`, `stage_counts`, `history_logs` и `alembic_version`.
- В `BACKLOG.md` задача `DB-002` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0009-alembic-bootstrap-db-002.md`;
  - `tasks/DB-002.md`.

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

### INIT-005

- Добавлен единый `Makefile` с quality gate командами для backend/frontend и общим таргетом `make quality`.
- Для backend добавлены format/lint команды на базе `ruff`:
  - зависимость `ruff` в `backend/pyproject.toml` (dev);
  - конфигурация `[tool.ruff]` для воспроизводимого поведения.
- Для frontend добавлены quality scripts:
  - `npm run format` (Prettier),
  - `npm run lint` (ESLint flat config + TypeScript),
  - `npm run build`,
  - `npm run test` (entrypoint для текущего этапа до добавления тестов).
- Добавлен frontend линт-конфиг `frontend/eslint.config.js`.
- `README.md` дополнен разделом `Quality Gates` с командами запуска.
- В `BACKLOG.md` задача `INIT-005` отмечена выполненной.

### INIT-006

- Добавлен отдельный frontend quality gate для строгой проверки типов:
  - `frontend/package.json`: новый script `typecheck` (`tsc --noEmit -p tsconfig.json`);
  - `Makefile`: добавлен таргет `frontend-typecheck` и включён в общий `quality`.
- Обновлён `README.md` в разделе `Quality Gates` с явной командой `make frontend-typecheck`.
- Для воспроизводимости в контейнере обновлён `ops/nginx/Dockerfile`: перед `npm run build` теперь выполняется `npm run typecheck`.
- Стабилизирован backend test gate в `Makefile`: `BACKEND_PYTHON` теперь автоматически использует `backend/.venv/bin/python`, если локальный venv существует (fallback на `python3` сохранён).
- В `BACKLOG.md` задача `INIT-006` отмечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0006-frontend-typecheck-gate-init-006.md`;
  - `tasks/INIT-006.md`.

### CLEAN-001

- Удалены неиспользуемые шаблонные файлы-заглушки:
  - `backend/alembic/.gitkeep`;
  - `backend/app/.gitkeep`;
  - `backend/tests/.gitkeep`;
  - `frontend/src/.gitkeep`.
- Удалён лишний служебный файл `blob`, не используемый приложением и процессом сборки.
- Усилен `.gitignore`:
  - добавлены шаблоны для секретов (`.env.*` с исключением `.env.example`);
  - добавлены артефакты разработки и сборки (`backend/.venv/`, `backend/*.egg-info/`, `frontend/node_modules/`, `frontend/dist/`, `.coverage`, `.DS_Store`).
- В `BACKLOG.md` задача `CLEAN-001` отмечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0007-clean-stage-a-hygiene.md`;
  - `tasks/CLEAN-001.md`.

### DB-001

- Реализована доменная константа стадий в backend (`backend/app/domain/stages.py`) как единый источник допустимых значений (`IN_BOX`, `BUILDING`, `PRIMING`, `PAINTING`, `DONE`).
- Добавлен слой моделей SQLAlchemy:
  - `backend/app/db/base.py` (декларативная база);
  - `backend/app/db/models.py` (`miniature_types`, `stage_counts`, `history_logs`);
  - `backend/app/db/__init__.py` для экспорта моделей.
- В моделях и миграции зафиксированы ключевые ограничения данных:
  - `UNIQUE` на `miniature_types.name`;
  - `CHECK stage_counts.count >= 0`;
  - `UNIQUE(type_id, stage_name)` для `stage_counts`;
  - `CHECK` на допустимые значения стадий для `stage_name`, `from_stage`, `to_stage`;
  - `FK` с `ON DELETE CASCADE` и индексы по `type_id`.
- Обновлён Alembic runtime:
  - `backend/alembic/env.py` теперь использует `Base.metadata`;
  - ревизия `backend/alembic/versions/0001_init_schema_placeholder.py` заменена с placeholder на создание целевой схемы БД.
- В `BACKLOG.md` задача `DB-001` отмечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0008-db-schema-and-constraints-db-001.md`;
  - `tasks/DB-001.md`.


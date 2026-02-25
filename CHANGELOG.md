# Changelog

## 2026-02-25

### API-004

- Реализован endpoint `GET /api/v1/types/{id}` в `backend/app/api/v1/router.py`:
  - добавлена выборка карточки типа по `id` с `LEFT JOIN` к `stage_counts`;
  - ответ возвращается в формате `TypeListItem` с гарантированным набором всех стадий;
  - при отсутствии типа возвращается `404` с сообщением `Type not found.`
- Выполнен рефакторинг сборки counts в `backend/app/api/v1/router.py`:
  - добавлены переиспользуемые helper-функции `_build_type_item` и `_apply_stage_count`;
  - устранено дублирование логики инициализации/заполнения стадий между `GET /types`, `GET /types/{id}` и `POST /types`.
- Добавлены интеграционные тесты `backend/tests/test_type_details_api.py`:
  - успешное получение карточки типа с заполненными и нулевыми стадиями;
  - корректный `404`-ответ для несуществующего типа.
- В `BACKLOG.md` задача `API-004` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0015-type-details-endpoint-api-004.md`;
  - `tasks/API-004.md`.

### API-003

- Реализован endpoint `POST /api/v1/types` в `backend/app/api/v1/router.py`:
  - добавлено создание нового типа миниатюр с ответом в формате `TypeListItem` и `201 Created`;
  - добавлена обработка нарушения уникальности имени с возвратом бизнес-кода `ERR_DUPLICATE_TYPE_NAME`;
  - для прочих ошибок целостности сохранено стандартное поведение (без маскировки в duplicate).
- Расширены API-схемы в `backend/app/api/v1/schemas.py`:
  - добавлена `TypeCreateRequest` со строгой валидацией (`strict=True`, `extra='forbid'`, trim строк) и ограничением длины имени.
- Добавлены интеграционные тесты `backend/tests/test_types_create_api.py`:
  - успешное создание типа возвращает нулевые counts по всем стадиям;
  - дублирующее имя возвращает `400` и `ERR_DUPLICATE_TYPE_NAME`;
  - подтверждено сидирование `stage_counts` при создании типа.
- В `BACKLOG.md` задача `API-003` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0014-create-type-endpoint-api-003.md`;
  - `tasks/API-003.md`.

### API-002

- Реализован endpoint `GET /api/v1/types` в `backend/app/api/v1/router.py`:
  - выборка типов выполняется с `LEFT JOIN` к `stage_counts`;
  - результат сортируется по `name ASC` (с дополнительной стабилизацией по `id ASC`);
  - ответ агрегирует количества по всем стадиям и гарантирует наличие всех 5 стадий в каждом элементе.
- Расширены API-схемы в `backend/app/api/v1/schemas.py`:
  - добавлены `TypeStageCounts`, `TypeListItem`, `TypeListResponse`.
- Добавлена инфраструктура DB-сессий `backend/app/db/session.py`:
  - DI-зависимость `get_db_session` для endpoint'ов;
  - lazy/cached фабрика сессий на основе `DATABASE_URL`.
- Добавлены интеграционные тесты `backend/tests/test_types_list_api.py`:
  - пустая БД возвращает `{"items": []}`;
  - выдача содержит все стадии в `counts` и отсортирована по имени.
- В `BACKLOG.md` задача `API-002` помечена выполненной.
- В `BACKLOG.md` добавлена задача `DOCS-002` (создание отсутствующего `AGENTS.md` как верхнего источника проектных инвариантов).
- Добавлены артефакты процесса:
  - `ADR/ADR-0013-types-list-endpoint-api-002.md`;
  - `tasks/API-002.md`.

### API-001

- Реализован базовый контракт ошибок API в `backend/app/api/v1/errors.py`:
  - добавлены коды ошибок `ERR_VALIDATION`, `ERR_INVALID_STAGE`, `ERR_INVALID_STAGE_TRANSITION`, `ERR_INSUFFICIENT_QTY`, `ERR_DUPLICATE_TYPE_NAME`;
  - добавлено единое исключение `ApiContractError` для бизнес-ошибок;
  - зарегистрированы глобальные обработчики ошибок для унифицированного JSON-формата (`code`, `message`) и HTTP 400 для бизнес-валидационных ошибок.
- Добавлены Pydantic-схемы API в `backend/app/api/v1/schemas.py`:
  - `ApiStatusResponse`, `ErrorResponse`, `TypeMoveRequest`;
  - `TypeMoveRequest` использует строгую валидацию (`strict=True`, `extra='forbid'`) и системные стадии через `StageCode`.
- Доменные стадии переведены на enum в `backend/app/domain/stages.py`:
  - введён `StageCode` как единый источник системных кодов стадий;
  - `STAGES` теперь формируется из `StageCode`.
- Обновлён `backend/app/api/v1/router.py`: `GET /api/v1/status` теперь использует `response_model=ApiStatusResponse`.
- Обновлён `backend/app/main.py`: зарегистрированы обработчики ошибок API-контрактов.
- Добавлены тесты `backend/tests/test_api_contracts.py`:
  - проверка единого формата бизнес-ошибок;
  - проверка единого формата ошибок валидации запроса;
  - проверка строгой валидации `TypeMoveRequest`.
- В `BACKLOG.md` задача `API-001` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0012-api-contracts-validation-and-error-format.md`;
  - `tasks/API-001.md`.

### CLEAN-002

- Централизован источник стадий в data-layer:
  - добавлен `STAGES_SQL_LIST` в `backend/app/domain/stages.py`;
  - SQLAlchemy-модели (`backend/app/db/models.py`) и миграция `backend/alembic/versions/0001_init_schema_placeholder.py` используют доменную константу вместо локальных строковых списков.
- Убрано дублирование стадий в миграции `backend/alembic/versions/0002_seed_stage_counts_on_type_insert.py`:
  - seed SQL для триггеров теперь генерируется из `STAGES`.
- Актуализирована индексация под целевой read-path истории:
  - удалены избыточные одиночные индексы по `stage_counts.type_id` и `history_logs.type_id`;
  - добавлен составной индекс `ix_history_logs_type_id_created_at`.
- Обновлён `backend/tests/test_migrations.py`: ожидания по стадиям формируются из доменной константы `STAGES`.
- В `BACKLOG.md` задача `CLEAN-002` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0011-clean-stage-b-stage-constants-and-indexes.md`;
  - `tasks/CLEAN-002.md`.

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


# Changelog

## 2026-02-25

### FE-004

- Реализовано создание типа миниатюр через модальное окно на главной странице:
  - добавлен компонент `CreateTypeModal` (`frontend/src/components/CreateTypeModal.tsx`) на базе нативного элемента `<dialog>`;
  - кнопки «Добавить тип» и CTA в empty state теперь открывают модалку вместо навигации на отдельную страницу;
  - после успешного создания модалка закрывается и список типов перезагружается — пользователь сразу видит новый тип.
- Обработка дубликатов:
  - при `ERR_DUPLICATE_TYPE_NAME` локализованное сообщение отображается внутри модалки через `getLocalizedErrorMessage`.
- Удалены устаревшие артефакты page-based подхода:
  - удалён файл `frontend/src/pages/CreateTypePage.tsx`;
  - удалён маршрут `/types/new` из `frontend/src/app/router.tsx`.
- Добавлены CSS-стили для модального окна в `frontend/src/styles.css`.
- Полный frontend quality gate пройден успешно:
  - `tsc --noEmit` (0 ошибок);
  - `eslint .` (0 ошибок);
  - `vite build` (dist/ собран).
- Backend тесты: 25 passed.
- В `BACKLOG.md` задача `FE-004` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0024-create-type-modal-fe-004.md`;
  - `tasks/FE-004.md`.

### FE-003

- Верифицирован DoD задачи FE-003 по реализации главной страницы из FE-001:
  - список типов сортируется по имени (backend `ORDER BY name ASC`);
  - поиск фильтрует список по названию (case-insensitive);
  - empty state при пустой базе содержит CTA «Добавить первый тип» без авто-открытия модалки.
- Исправлен UX-дефект пустого поиска:
  - добавлен i18n-ключ `pages.main.emptySearch` в оба словаря (`ru.ts`, `en.ts`);
  - `MainPage.tsx` теперь показывает «Ничего не найдено.» / «No results found.» при пустом результате поиска вместо «Типов пока нет.».
- Полный frontend quality gate пройден успешно:
  - `tsc --noEmit` (0 ошибок);
  - `eslint .` (0 ошибок);
  - `vite build` (dist/ собран).
- Backend тесты: 25 passed.
- В `BACKLOG.md` задача `FE-003` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0023-main-screen-empty-search-state-fe-003.md`;
  - `tasks/FE-003.md`.

### FE-002

- Добавлены типы для запроса импорта в `frontend/src/shared/api/types.ts`:
  - `ImportStageCount`, `ImportHistoryItem`, `ImportTypeItem`, `ImportRequest` — зеркалят Pydantic-схемы backend.
- Типизирован метод `importState` в `frontend/src/shared/api/client.ts`:
  - сигнатура изменена с `data: unknown` на `data: ImportRequest`.
- Создан централизованный хелпер `getLocalizedErrorMessage` в `frontend/src/shared/api/errors.ts`:
  - инкапсулирует маппинг кодов ошибок API через i18n-словари;
  - устраняет дублирование логики обработки ошибок в компонентах.
- Рефакторинг трёх страниц (`MainPage`, `CreateTypePage`, `TypeDetailsPage`) для использования централизованного хелпера:
  - убран прямой импорт `ApiClientError` из компонентов;
  - обработка ошибок сведена к однострочному вызову `getLocalizedErrorMessage(err, t)`.
- Полный frontend quality gate пройден успешно:
  - `tsc --noEmit` (0 ошибок);
  - `eslint .` (0 ошибок);
  - `vite build` (dist/ собран).
- Backend тесты: 25 passed.
- В `BACKLOG.md` задача `FE-002` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0022-typed-api-client-error-mapping-fe-002.md`;
  - `tasks/FE-002.md`.

### FE-001

- Расширены i18n-словари (`ru.ts`, `en.ts`) до полного набора ключей:
  - названия стадий (`stages.IN_BOX`, …, `stages.DONE`);
  - маппинг кодов ошибок backend (`errors.ERR_INSUFFICIENT_QTY`, …);
  - подписи для всех страниц, кнопок, форм, экспорта/импорта.
- Исправлен API-клиент (`shared/api/client.ts`):
  - поле ответа ошибки исправлено с `detail` на `message` (соответствие backend контракту);
  - добавлены типизированные методы для всех 7 endpoint'ов v1.
- Добавлены доменные типы фронтенда (`shared/api/types.ts`):
  - `StageCode`, `STAGES`, `STAGE_INDEX` и интерфейсы для всех API-ответов/запросов.
- Обновлён `AppLayout`: убрана демо-навигация, заголовок — ссылка на главную.
- Реализован `MainPage`:
  - загрузка списка типов через API с отображением стадий;
  - поиск по имени;
  - empty state с CTA «Добавить первый тип».
- Реализован `CreateTypePage`:
  - форма создания типа с обработкой ошибки дубликата имени;
  - редирект на карточку после создания.
- Реализован `TypeDetailsPage`:
  - отображение counts по стадиям;
  - форма перемещения (from → to, qty с ограничением по доступному);
  - секция истории с отображением сгруппированных записей;
  - обработка 404.
- Обновлён роутер: добавлен маршрут `/types/new` (перед `:typeId`).
- Обновлены стили: CSS-переменные, карточки, формы, бейджи стадий, history.
- Полный frontend quality gate пройден успешно:
  - `tsc --noEmit` (0 ошибок);
  - `eslint .` (0 ошибок);
  - `vite build` (dist/ собран).
- Backend тесты: 25 passed.
- В `BACKLOG.md` задача `FE-001` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0021-frontend-app-scaffold-fe-001.md`;
  - `tasks/FE-001.md`.

### CLEAN-003

- Проведена приборка backend-слоя для этапа C в `backend/app/api/v1/router.py`:
  - устранено дублирование маппинга стадий в поля ответа (`TypeStageCounts`) через единый словарь `STAGE_COUNT_FIELD_BY_STAGE`;
  - сборка `TypeStageCounts` централизована в helper `_stage_counts_model_from_dict`, чтобы убрать ручное заполнение каждого поля в нескольких местах;
  - упрощена import-логика `_build_stage_delta_map` после централизации валидации в схемах.
- Централизована валидация импортируемых stage counts в `backend/app/api/v1/schemas.py`:
  - для `ImportTypeItem` добавлен `model_validator`, который требует наличие всех системных стадий ровно по одному разу;
  - тем самым проверка полноты/уникальности стадий перенесена из роутера в слой схем.
- Усилен security-профиль локального окружения:
  - в `backend/app/main.py` включен `CORSMiddleware` с явным allowlist локальных origin;
  - в `backend/app/config.py` добавлена конфигурация `cors_allowed_origins` с безопасными значениями по умолчанию для localhost;
  - в `ops/nginx/default.conf` добавлен безопасный redirect `/api -> /api/`, proxy ограничен префиксом `^~ /api/`, отключен `proxy_redirect`.
- Добавлены проверки в тестах:
  - `backend/tests/test_app.py` — позитивный/негативный CORS-кейсы для разрешенного и неразрешенного origin;
  - `backend/tests/test_import_api.py` — отклонение импорта при неполном наборе `stage_counts`.
- Полный backend quality gate пройден успешно:
  - `make backend-lint`
  - `make backend-test` (25 passed).
- В `BACKLOG.md` задача `CLEAN-003` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0020-clean-stage-c-validation-cors-proxy.md`;
  - `tasks/CLEAN-003.md`.

### API-008

- Реализован endpoint `POST /api/v1/import` в `backend/app/api/v1/router.py`:
  - добавлен импорт JSON с merge по имени типа (`miniature_types.name`);
  - при совпадении имени выполняется суммирование `stage_counts` по стадиям и append истории в `history_logs`;
  - при отсутствии типа создается новый тип и к нему применяется импортируемое состояние;
  - весь импорт выполняется в одной транзакции (`all-or-nothing`) с откатом при любой ошибке.
- Добавлена явная бизнес-ошибка формата импорта:
  - в `backend/app/api/v1/errors.py` добавлен код `ERR_INVALID_IMPORT_FORMAT`;
  - некорректный payload импорта возвращает `400` с предсказуемым контрактом ошибки.
- Расширены API-схемы в `backend/app/api/v1/schemas.py`:
  - добавлены модели `ImportStageCount`, `ImportHistoryItem`, `ImportTypeItem`, `ImportRequest`, `ImportResponse`.
- Добавлены интеграционные тесты `backend/tests/test_import_api.py`:
  - проверка merge-семантики (суммы counts и append истории);
  - проверка `all-or-nothing` rollback при частично некорректном payload.
- В `BACKLOG.md` задача `API-008` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0019-import-endpoint-api-008.md`;
  - `tasks/API-008.md`.

### API-007

- Реализован endpoint `GET /api/v1/export` в `backend/app/api/v1/router.py`:
  - добавлена выгрузка полного состояния по всем типам с детерминированной сортировкой по имени типа (`name ASC`);
  - в экспорт включены текущие counts по всем системным стадиям и полная сырая история перемещений;
  - история в рамках каждого типа отдается в стабильном порядке (`created_at ASC`, затем `id ASC`).
- Расширены API-схемы в `backend/app/api/v1/schemas.py`:
  - добавлены модели экспорта `ExportStageCount`, `ExportHistoryItem`, `ExportTypeItem`, `ExportResponse`.
- Добавлены интеграционные тесты `backend/tests/test_export_api.py`:
  - проверка пустой БД (`types: []`);
  - проверка выгрузки типов, stage_counts и истории в одном ответе.
- В `BACKLOG.md` задача `API-007` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0018-export-endpoint-api-007.md`;
  - `tasks/API-007.md`.

### API-006

- Реализован endpoint `GET /api/v1/types/{id}/history` в `backend/app/api/v1/router.py`:
  - добавлена выборка сырых событий `history_logs` с сортировкой по времени (`created_at`, `id`);
  - добавлена read-time группировка соседних событий по правилам PRD (`одинаковый from->to` и разница между соседними событиями `<= 300` секунд);
  - `timestamp` группы фиксируется как время первого события группы;
  - для несуществующего типа возвращается `404` (`Type not found.`), для существующего без истории — пустой список групп.
- Расширены API-схемы `backend/app/api/v1/schemas.py`:
  - добавлены `TypeHistoryGroup` и `TypeHistoryResponse`.
- Добавлены интеграционные тесты `backend/tests/test_type_history_api.py`:
  - подтверждены граничные условия группировки `299/300/301` секунд;
  - подтверждено правило «группируем только соседние события» (несоседние одинаковые переходы не объединяются).
- В `BACKLOG.md` задача `API-006` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0017-history-read-time-grouping-api-006.md`;
  - `tasks/API-006.md`.

### API-005

- Реализован endpoint `POST /api/v1/types/{id}/move` в `backend/app/api/v1/router.py`:
  - добавлена проверка направления перехода строго вперёд по pipeline с ошибкой `ERR_INVALID_STAGE_TRANSITION`;
  - добавлена атомарная обработка перемещения со строковой блокировкой `stage_counts` через `SELECT ... FOR UPDATE`;
  - при недостатке в источнике возвращается `400` с кодом `ERR_INSUFFICIENT_QTY`;
  - при успешном перемещении обновляются оба счётчика, создаётся запись в `history_logs`, возвращаются актуальные counts.
- Выполнен рефакторинг получения карточки типа:
  - добавлены helper-функции `_iter_type_rows_by_id` и `_build_type_item_by_id` в `backend/app/api/v1/router.py`;
  - `GET /api/v1/types/{id}` переведён на переиспользование новой логики, чтобы убрать дублирование.
- В доменной модели стадий `backend/app/domain/stages.py` добавлены:
  - индекс порядка стадий `STAGE_INDEX`;
  - helper `is_forward_transition` как единая проверка допустимого направления перехода.
- Добавлены интеграционные тесты `backend/tests/test_type_move_api.py`:
  - успешное перемещение с проверкой итоговых counts и записи в `history_logs`;
  - ошибка `ERR_INSUFFICIENT_QTY` при нехватке количества;
  - ошибка `ERR_INVALID_STAGE_TRANSITION` для перехода назад.
- В `BACKLOG.md` задача `API-005` помечена выполненной.
- Добавлены артефакты процесса:
  - `ADR/ADR-0016-atomic-forward-move-endpoint-api-005.md`;
  - `tasks/API-005.md`.

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


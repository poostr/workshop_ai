# Отчёт по задаче CLEAN-003

## Статус

Выполнено.

## Что сделано

- Выполнена приборка backend API в `backend/app/api/v1/router.py`:
  - убрано дублирование маппинга стадий в `TypeStageCounts`;
  - добавлен единый маппинг `STAGE_COUNT_FIELD_BY_STAGE`;
  - добавлен helper `_stage_counts_model_from_dict` для централизованной сборки counts.
- Централизованы валидации импортируемых данных в `backend/app/api/v1/schemas.py`:
  - для `ImportTypeItem` добавлен `model_validator` с инвариантом "все стадии присутствуют ровно по одному разу";
  - роутер больше не повторяет проверку полноты/уникальности стадий.
- Проведён security check локальной конфигурации:
  - в `backend/app/main.py` добавлен `CORSMiddleware` с allowlist локальных origin;
  - в `backend/app/config.py` добавлен параметр `cors_allowed_origins`;
  - в `ops/nginx/default.conf` уточнён proxy-path (`/api -> /api/`, `^~ /api/`, `proxy_redirect off`).
- Добавлены тесты:
  - `backend/tests/test_app.py` — разрешённый/запрещённый origin для CORS;
  - `backend/tests/test_import_api.py` — отклонение импорта при неполном наборе стадий.
- В `BACKLOG.md` задача `CLEAN-003` отмечена выполненной.
- В `CHANGELOG.md` добавлена запись о задаче.

## Верификация

- `make quality` — успешно (backend format/lint/tests, frontend format/lint/typecheck/build/test).
- `backend` тесты: 25 passed.

## Принятые решения

- ADR: [`ADR-0020`](../ADR/ADR-0020-clean-stage-c-validation-cors-proxy.md)

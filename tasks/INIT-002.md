# Отчёт по задаче INIT-002

## Статус

Выполнено.

## Что сделано

- Поднят минимальный backend на FastAPI:
  - `GET /health` для контейнерного health-check и проверки жизнеспособности;
  - базовый роутер под префиксом `/api/v1` (`GET /api/v1/status`).
- Реализовано чтение конфигурации из переменных окружения через `pydantic-settings`:
  - `APP_ENV`
  - `LOG_LEVEL`
  - `DATABASE_URL`
- Добавлены базовые backend-артефакты:
  - `backend/pyproject.toml`
  - `backend/Dockerfile`
- Обновлён `docker-compose.yml` для старта backend контейнера и healthcheck.
- Добавлены минимальные автотесты backend:
  - `backend/tests/test_app.py`
  - `backend/tests/conftest.py`
- В `BACKLOG.md` задача `INIT-002` отмечена выполненной.

## Верификация

- `docker compose build app && docker compose run --rm app pytest` — успешно, `2 passed`.
- `docker compose up -d app` + `curl http://localhost:8000/health` — успешно, ответ `{"status":"ok","env":"dev"}`.

## Принятые решения

- ADR: [`ADR-0002`](../ADR/ADR-0002-backend-bootstrap-init-002.md)


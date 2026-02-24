# Отчёт по задаче INIT-004

## Статус

Выполнено.

## Что сделано

- Обновлён `docker-compose.yml` под целевую схему из трёх сервисов: `app`, `postgres`, `nginx`.
- Реализован автопрогон миграций при старте `app`:
  - добавлен `backend/entrypoint.sh` (`alembic upgrade head` перед запуском API);
  - обновлён `backend/Dockerfile`.
- Добавлена базовая инфраструктура Alembic:
  - `backend/alembic.ini`;
  - `backend/alembic/env.py`;
  - `backend/alembic/versions/0001_init_schema_placeholder.py`.
- Переведён `nginx` на сборку собственного образа:
  - `ops/nginx/Dockerfile` (multi-stage build фронтенда и копирование `dist` в nginx image).
- Добавлен `.dockerignore` для уменьшения контекста сборки и ускорения CI/локальных сборок.
- В `BACKLOG.md` задача `INIT-004` помечена как выполненная.

## Верификация

- `docker compose up --build -d` — успешно, подняты `app`, `postgres`, `nginx`.
- `docker compose logs app --tail=80` — подтверждён запуск `alembic upgrade head`.
- `curl http://localhost:8080/` — nginx отдаёт SPA.
- `curl http://localhost:8080/api/v1/status` — проксирование API через nginx работает.
- `docker compose run --rm app pytest` — успешно, `2 passed`.
- `cd frontend && npm run build` — успешно.

## Принятые решения

- ADR: [`ADR-0004`](../ADR/ADR-0004-docker-compose-init-004.md)

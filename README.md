# Miniatures Progress Tracker (v1)

Локальный инструмент для учёта миниатюр по стадиям пайплайна.

## Быстрый старт

1. Скопируйте пример переменных окружения:
   - `cp .env.example .env`
2. Запустите сервисы:
   - `docker compose up --build`

## Сервисы и хранилище

- `app` — backend (FastAPI)
- `postgres` — база данных
- `nginx` — раздача frontend-статики и проксирование API

Данные PostgreSQL сохраняются в Docker volume (имя volume задаётся в `docker-compose.yml`).

## Важно про данные

Команда `docker compose down -v` удаляет контейнеры **и volume с базой**, это приведёт к потере локальных данных.

Перед потенциально рискованными операциями делайте экспорт данных из приложения.

## Quality Gates

- Backend:
  - `make backend-format`
  - `make backend-lint`
  - `make backend-test`
- Frontend:
  - `make frontend-format`
  - `make frontend-lint`
  - `make frontend-build`
  - `make frontend-test`
- Полный прогон всех quality gates:
  - `make quality`


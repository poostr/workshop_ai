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

## E2E Smoke Test

Минимальный сценарий проверки полного цикла:
создание типа → перемещение → экспорт → импорт (merge) → проверка истории.

1. Поднимите стек: `docker compose up --build -d`
2. Запустите smoke-тест:
   - Напрямую к backend: `make e2e-smoke`
   - Через nginx: `make e2e-smoke E2E_BASE_URL=http://localhost:8080/api/v1`

Тест создаёт тип с уникальным именем (с временной меткой), не загрязняя рабочие данные.

### Ручной чеклист (альтернатива)

1. Открыть `http://localhost:8080` — главная страница (empty state с CTA)
2. Создать тип миниатюр (например, «Space Marines»)
3. На карточке типа выполнить перемещение IN_BOX → BUILDING
4. Проверить, что counts обновились
5. Перейти в секцию History — убедиться, что запись появилась
6. На главной экспортировать JSON (кнопка «Экспорт»)
7. Импортировать этот же JSON — убедиться, что counts удвоились
8. Переключить язык RU/EN — убедиться, что UI переключается без потери данных

## Quality Gates

- Backend:
  - `make backend-format`
  - `make backend-lint`
  - `make backend-test`
- Frontend:
  - `make frontend-format`
  - `make frontend-lint`
  - `make frontend-typecheck`
  - `make frontend-build`
  - `make frontend-test`
- Полный прогон всех quality gates:
  - `make quality`


# Отчёт по задаче INIT-003

## Статус

Выполнено.

## Что сделано

- Поднят frontend на `React + TypeScript + Vite`.
- Реализован базовый роутинг:
  - `/` -> страница-заглушка `Main`;
  - `/types/:typeId` -> страница-заглушка `TypeDetails`.
- Добавлен базовый layout с переключателем языка RU/EN.
- Подготовлен i18n-каркас:
  - подключены `i18next` и `react-i18next`;
  - добавлены словари `ru/en`;
  - UI-строки вынесены в переводные ключи.
- Добавлен каркас API-клиента:
  - базовый `ApiClient`;
  - централизованная обработка backend error codes.
- Обновлён `BACKLOG.md`:
  - `INIT-003` помечена выполненной;
  - добавлена новая задача `INIT-006` на отдельный quality gate для typecheck.

## Верификация

- `cd frontend && npm install` — успешно.
- `cd frontend && npm run build` — успешно, артефакты в `frontend/dist/`.
- `docker compose run --rm app pytest` — успешно, `2 passed`.

## Принятые решения

- ADR: [`ADR-0003`](../ADR/ADR-0003-frontend-bootstrap-init-003.md)

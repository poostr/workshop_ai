# Отчёт по задаче INIT-006

## Статус

Выполнено.

## Что сделано

- Добавлен отдельный frontend typecheck gate:
  - `frontend/package.json`: script `typecheck` (`tsc --noEmit -p tsconfig.json`).
- Обновлён корневой `Makefile`:
  - добавлен таргет `frontend-typecheck`;
  - таргет включён в `make quality`.
- Обновлён `README.md`:
  - в разделе `Quality Gates` добавлена команда `make frontend-typecheck`.
- Усилена контейнерная проверка:
  - в `ops/nginx/Dockerfile` перед `npm run build` добавлен `npm run typecheck`.
- Для воспроизводимого прогона тестов в текущем окружении обновлён `Makefile`:
  - `BACKEND_PYTHON` автоматически использует `backend/.venv/bin/python`, если локальный venv присутствует (иначе остаётся `python3`).
- В `BACKLOG.md` задача `INIT-006` помечена выполненной.

## Верификация

- `make frontend-typecheck` — успешно.
- `make frontend-build` — успешно.
- `make frontend-lint` — успешно.
- `make frontend-test` — успешно.
- `docker compose build nginx` — успешно (внутри стадии сборки выполнен `npm run typecheck`).
- `make backend-test` — успешно.

## Принятые решения

- ADR: [`ADR-0006`](../ADR/ADR-0006-frontend-typecheck-gate-init-006.md)

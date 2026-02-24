# INIT-005 — Quality gates (format/lint/test entrypoints)

## Что сделано

- Добавлен `Makefile` в корне проекта с едиными командами quality gates:
  - `backend-format`, `backend-lint`, `backend-test`;
  - `frontend-format`, `frontend-lint`, `frontend-build`, `frontend-test`;
  - `quality` для полного прогона.
- Backend:
  - добавлена dev-зависимость `ruff`;
  - добавлена базовая конфигурация `ruff` в `backend/pyproject.toml`.
- Frontend:
  - добавлены scripts `format`, `lint`, `test` в `frontend/package.json`;
  - добавлены dev-зависимости для линтинга/форматирования (`eslint`, `typescript-eslint`, `prettier` и др.);
  - добавлен `frontend/eslint.config.js`.
- `README.md` дополнен инструкциями по запуску quality gates.

## Проверка

- Выполнен полный прогон `make quality`:
  - backend format/lint/test — успешно;
  - frontend format/lint/build/test — успешно.

## Артефакты решений

- [ADR-0005: Quality gates для INIT-005](../ADR/ADR-0005-quality-gates-init-005.md)

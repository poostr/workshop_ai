# ADR-0006: Отдельный frontend typecheck gate для INIT-006

- Статус: Accepted
- Дата: 2026-02-24
- Связанная задача: INIT-006

## Контекст

На этапе bootstrap уже есть frontend quality gates (`format`, `lint`, `build`, `test`), но нет отдельного воспроизводимого шага строгой типовой проверки TypeScript. Это затрудняет раннее обнаружение типовых ошибок и размывает ответственность между build и typecheck.

Требование задачи `INIT-006`: добавить отдельную команду typecheck и обеспечить стабильный проход как локально, так и в контейнерной среде.

## Решение

1. Добавить отдельный npm script:
   - `typecheck`: `tsc --noEmit -p tsconfig.json`.
2. Добавить root-level make target:
   - `make frontend-typecheck`.
3. Включить `frontend-typecheck` в агрегирующий `make quality`.
4. В контейнерной сборке frontend (`ops/nginx/Dockerfile`) запускать `npm run typecheck` перед `npm run build`.

## Последствия

- Положительные:
  - Типовые ошибки выявляются отдельным, прозрачным quality gate.
  - Проверка типов запускается одинаково локально и в контейнере.
  - CI/локальный процесс получает явный контракт для type safety.
- Ограничения:
  - Немного увеличивается время frontend сборки в Docker из-за дополнительного шага `typecheck`.

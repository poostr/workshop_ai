# Отчёт по задаче CLEAN-002

## Статус

Выполнено.

## Что сделано

- Устранено дублирование строковых значений стадий в data-layer:
  - добавлена доменная константа `STAGES_SQL_LIST` в `backend/app/domain/stages.py`;
  - модели `backend/app/db/models.py` используют `STAGES_SQL_LIST` для `CHECK`-ограничений;
  - миграция `backend/alembic/versions/0001_init_schema_placeholder.py` переведена на `STAGES_SQL_LIST`;
  - миграция `backend/alembic/versions/0002_seed_stage_counts_on_type_insert.py` генерирует SQL-вставки из `STAGES`, без хардкода стадий.
- Приведена индексация к целевым запросам этапа B:
  - удалены избыточные одиночные индексы по `stage_counts.type_id` и `history_logs.type_id`;
  - добавлен составной индекс `ix_history_logs_type_id_created_at`.
- Обновлён тест `backend/tests/test_migrations.py`: ожидания по стадиям формируются из `STAGES`.
- В `BACKLOG.md` задача `CLEAN-002` помечена выполненной.
- В `CHANGELOG.md` добавлена запись по `CLEAN-002`.

## Верификация

- `make quality` — успешно (backend format/lint/tests, frontend format/lint/typecheck/build/test).

## Принятые решения

- ADR: [`ADR-0011`](../ADR/ADR-0011-clean-stage-b-stage-constants-and-indexes.md)

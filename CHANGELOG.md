# Changelog

## 2026-02-24

### INIT-001

- Создан базовый каркас репозитория: `backend/`, `frontend/`, `ops/`.
- Добавлены базовые инфраструктурные файлы: `README.md`, `.env.example`, `.gitignore`, `docker-compose.yml`.
- Добавлен стартовый nginx-конфиг: `ops/nginx/default.conf`.
- Добавлены процессные артефакты: `ADR/ADR-0001-repo-scaffold.md`, `tasks/INIT-001.md`.
- В `BACKLOG.md` задача `INIT-001` отмечена как выполненная.

### INIT-002

- Реализован backend bootstrap на FastAPI:
  - `backend/app/main.py` (`create_app`, `GET /health`);
  - `backend/app/config.py` (чтение `APP_ENV`, `LOG_LEVEL`, `DATABASE_URL` из env);
  - `backend/app/api/v1/router.py` (базовый v1-роутер).
- Добавлены backend зависимости и контейнеризация:
  - `backend/pyproject.toml`;
  - `backend/Dockerfile`.
- Обновлён `docker-compose.yml`:
  - app сервис теперь собирается из `backend/Dockerfile` и поднимает API на `8000`;
  - добавлен healthcheck app;
  - убран проброс `5432:5432` у postgres для устранения локального порт-конфликта.
- Добавлены тесты backend:
  - `backend/tests/test_app.py`;
  - `backend/tests/conftest.py`.
- В `BACKLOG.md` задача `INIT-002` отмечена как выполненная.
- Добавлены артефакты процесса:
  - `ADR/ADR-0002-backend-bootstrap-init-002.md`;
  - `tasks/INIT-002.md`.


BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_PYTHON ?= $(if $(wildcard $(BACKEND_DIR)/.venv/bin/python),.venv/bin/python,python3)

.PHONY: quality backend-format backend-lint backend-test frontend-format frontend-lint frontend-typecheck frontend-build frontend-test e2e-smoke

quality: backend-format backend-lint backend-test frontend-format frontend-lint frontend-typecheck frontend-build frontend-test

backend-format:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m ruff format app tests

backend-lint:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m ruff check app tests

backend-test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-app

frontend-format:
	cd $(FRONTEND_DIR) && npm run format

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

frontend-typecheck:
	cd $(FRONTEND_DIR) && npm run typecheck

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

frontend-test:
	cd $(FRONTEND_DIR) && npm run test

e2e-smoke:
	python3 tests/e2e_smoke.py $(E2E_BASE_URL)

BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_PYTHON ?= python3

.PHONY: quality backend-format backend-lint backend-test frontend-format frontend-lint frontend-build frontend-test

quality: backend-format backend-lint backend-test frontend-format frontend-lint frontend-build frontend-test

backend-format:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m ruff format app tests

backend-lint:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m ruff check app tests

backend-test:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m pytest

frontend-format:
	cd $(FRONTEND_DIR) && npm run format

frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

frontend-test:
	cd $(FRONTEND_DIR) && npm run test

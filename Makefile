.PHONY: seed reset-demo test run evaluate

# ── Schema and seed data ──────────────────────────────────────────────────────

seed:
	cd backend && python -m scripts.init_db

reset-demo:
	cd backend && python -m scripts.init_db --reset

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd backend && python -m pytest tests/ -v

test-fast:
	cd backend && python -m pytest tests/ -v -x

# ── Run (development) ─────────────────────────────────────────────────────────

run-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

# Run both in separate terminals; for convenience use Docker Compose in production.
run:
	@echo "Run 'make run-backend' and 'make run-frontend' in separate terminals."
	@echo "Or: docker compose up --build"

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# ── Evaluation (Phase 9 — requires Phase 8 anomaly model) ─────────────────────

evaluate:
	cd backend && python -m scripts.evaluate_anomaly && python -m scripts.evaluate

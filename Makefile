.PHONY: dev up down build test lint clean

# ── Docker ────────────────────────────────────

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart: down up

# ── Dev ───────────────────────────────────────

dev: up
	@echo "CIOTX running at:"
	@echo "  Dashboard: http://localhost:3000"
	@echo "  API:       http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"

# ── Quality Gates ─────────────────────────────

lint:
	cd api && ruff check app/
	cd dashboard && npx eslint app/

test:
	cd api && python -m pytest tests/ -v
	cd dashboard && npx jest --passWithNoTests
	cd cli && go test ./...

typecheck:
	cd api && mypy app/
	cd dashboard && npx tsc --noEmit

build:
	docker compose build

check: lint test typecheck build
	@echo "✅ All gates passed. Ready to push."

# ── Docker Cleanup ────────────────────────────

clean:
	docker compose down -v
	rm -rf pgdata/ redisdata/

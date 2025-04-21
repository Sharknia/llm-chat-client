run:
	poetry run uvicorn app.main:app --reload

# Docker Compose 로 개발 환경 실행
dev:
	@echo "Starting services with Docker Compose..."
	@echo "Ensure .env file is created and configured."
	docker compose up --build

example:
	poetry run python exmaple.py
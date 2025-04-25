# Docker 이미지 이름 설정 (원하는 이름으로 변경 가능)
IMAGE_NAME = crobat-server-image
CONTAINER_NAME = crobat-server-container

# Docker Compose 로 개발 환경 실행
dev:
	@echo "Starting services with Docker Compose..."
	@echo "Ensure .env file is created and configured."
	docker compose up --build

example:
	poetry run python exmaple.py

# --- Docker 관련 명령어 추가 ---
docker-build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) .

docker-run:
	@echo "Running Docker container..."
	# 기존 컨테이너가 있으면 중지 및 삭제
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	# 새 컨테이너 실행 (백그라운드, 포트 8000 매핑, .env 파일 마운트)
	docker run -d --name $(CONTAINER_NAME) -p 8000:8000 --env-file .env $(IMAGE_NAME)

docker-stop:
	@echo "Stopping Docker container..."
	docker stop $(CONTAINER_NAME)

docker-logs:
	@echo "Showing Docker container logs..."
	docker logs -f $(CONTAINER_NAME)

docker-clean:
	@echo "Removing Docker container..."
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Removing Docker image..."
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

.PHONY: dev example docker-build docker-run docker-stop docker-logs docker-clean
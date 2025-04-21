#!/bin/sh

# 데이터베이스 마이그레이션 실행
# 컨테이너 내부에서 실행되므로 .env 파일의 DATABASE_URL을 사용함 (alembic/env.py가 로드)
echo "Running database migrations..."
alembic upgrade head

# 원래 CMD 실행 ($@는 Dockerfile의 CMD 인자들을 나타냄)
echo "Starting application..."
exec "$@" 
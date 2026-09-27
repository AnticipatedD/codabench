#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker-compose.test.yml"

echo "Starting test stack..."
docker compose -f "$COMPOSE_FILE" up -d --build

echo "Waiting for Django health endpoint..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "Django is healthy"
    break
  fi
  if [[ $i -eq 30 ]]; then
    echo "Timed out waiting for health endpoint"
    docker compose -f "$COMPOSE_FILE" logs
    exit 1
  fi
  sleep 5
done

echo "Running tests..."
# Adjust the pytest path if your e2e tests live elsewhere
docker compose -f "$COMPOSE_FILE" exec -T django \
  pytest tests/ -v --tb=short || {
    echo "Tests failed"
    docker compose -f "$COMPOSE_FILE" down -v
    exit 1
  }

echo "Cleaning up..."
docker compose -f "$COMPOSE_FILE" down -v
echo "All tests passed."

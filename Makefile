.PHONY: help build up down logs test lint

help:
	@echo "build  build the Docker image for this machine"
	@echo "up     build and start the container (needs .env.local)"
	@echo "down   stop and remove the container"
	@echo "logs   follow the container logs"
	@echo "test   run pytest"
	@echo "lint   run ruff"

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f nbe

test:
	python3 -m pytest -q

lint:
	ruff check src tests custom_components

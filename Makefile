.PHONY: runserver test db-down db-up db-reset

runserver:
	poetry run python manage.py runserver

test:
	poetry run python manage.py test

migrate:
	poetry run python manage.py migrate

db-down:
	docker compose down --remove-orphans

db-up:
	docker compose up -d

db-reset:
	docker compose down --volumes --rmi all --remove-orphans
	docker compose up -d

.PHONY: runserver test

runserver:
	python manage.py runserver

test:
	python manage.py test

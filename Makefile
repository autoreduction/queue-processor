all:
	python setup.py sdist bdist_wheel
	twine upload --repository pypi dist/*
	rm -r build/ dist

kafka:
	docker-compose -f container/docker-compose.yml up -d

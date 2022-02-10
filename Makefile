all:
	python setup.py sdist bdist_wheel
	twine upload --repository pypi dist/*
	rm -r build/ dist

activemq:
	sudo docker run --rm --name activemq -p 61613:61613 -p 8161:8161 -d rmohr/activemq

kafka:
	docker-compose -f container/docker-compose.yml up -d

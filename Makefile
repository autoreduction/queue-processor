all:
	python3 -m build
	python3 -m twine upload --repository pypi dist/*
	rm -r build/ dist

kafka_client:
	docker run -d --pull=always --name=redpanda-1 --rm \
-p 9092:9092 \
-p 9644:9644 \
docker.vectorized.io/vectorized/redpanda:latest \
redpanda start \
--overprovisioned \
--smp 1  \
--memory 1G \
--reserve-memory 0M \
--node-id 0 \
--check=false

# Create client first, then initialise the topic to be used
kafka: kafka_client
# Sleep for a couple of seconds to allow host ports to be opened
	sleep 3
	docker exec -it redpanda-1 \
rpk topic create data_ready --brokers=localhost:9092

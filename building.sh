#!/bin/bash
docker run -d --name kafka -p 9092:9092 apache/kafka:3.8.0
sleep 5
docker  exec -it kafka  sh -c "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic attempt --partitions 3"
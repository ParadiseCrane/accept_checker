"""Contains Listener for database updates class"""

import os
import logging
import json
import uuid

from typing import Any
from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from utils.basic import map_attempt_status
from models import (
    Attempt,
    Task,
    Checker,
    Language,
    TaskTest,
    Constraints,
)

from manager import Manager
from local_secrets import SECRETS_MANAGER
from settings import SETTINGS_MANAGER

def create_topic(kafka_connection: str):
    global topic
    a = AdminClient({'bootstrap.servers': kafka_connection})
    new_topics = [NewTopic("attempt_checker", num_partitions=12)]

    fs = a.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))

class Listener:
    """Listens to database updates"""

    _manager_path = os.path.join(".", "manager.py")

    def __init__(self, logger: logging.Logger):
        self.logging = logger
        self._manager = Manager()
        self._kafka_string = SECRETS_MANAGER.kafka_string
        self._debug = SECRETS_MANAGER.debug

        self._current_dir = os.path.dirname(os.path.abspath(__file__))

        self.settings = SETTINGS_MANAGER.listener
        self.cpu_number = os.cpu_count() or 0
        self.busy_cpu = 0
        self.max_workers = max(
            2,
            int(self.cpu_number * self.settings.cpu_utilization_fraction),
        )
        create_topic(self._kafka_string)
        self.producer = Producer({'bootstrap.servers': self._kafka_string})
        self.consumer = Consumer({
            'bootstrap.servers': self._kafka_string,
            "client.id": uuid.uuid4(),
            'group.id': 'checker',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(["attempt_checker"])
        self.running = True

    def __del__(self):
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()

    def produce(self, topic: str, data: dict[str, Any]):
        payload = json.dumps(data).encode("utf-8")
        self.producer.produce(
            topic,
            payload,
            key=data["spec"]
        )
        self.producer.flush()

    def set_testing(self, attempt: dict[str, Any]):
        self.logging.info(f"Set status of attempt `{attempt["spec"]}` to `testing`")
        self.produce("attempt_status", {"spec": attempt["spec"], "status": map_attempt_status("testing")})

    def set_finished(self, tested_attempt: dict[str, Any]):
        self.logging.info(f"Set status of attempt `{tested_attempt["spec"]}` to `finished`")
        self.produce("attempt_status", {"spec": tested_attempt["spec"], "status": map_attempt_status("finished")})

    def sink_attempt(self, tested_attempt: dict[str, Any]):
        self.logging.info(f"Saving data fo tested attempt `{tested_attempt["spec"]}`")
        self.produce("attempt_sink", tested_attempt)

    def detect_ai(self, tested_attempt: dict[str, Any]):
        self.logging.info(f"Sending attempt `{tested_attempt["spec"]}` to detect ai")
        self.produce("attempt_detect_ai", tested_attempt)

    def test_attempt(self, kafka_attempt: dict[str, Any]) -> dict[str, Any]:
        self.logging.info(f"Testing attempt `{kafka_attempt["spec"]}`")
        # TODO: validate json

        attempt = Attempt(**kafka_attempt)
        attempt.language = Language(**kafka_attempt["language"])
        attempt.task = Task(**kafka_attempt["task"])
        attempt.task.constraints = Constraints(**kafka_attempt["task"]["constraints"])
        attempt.task.tests = [
            TaskTest(**task_test) for task_test in kafka_attempt["task"]["tests"]
        ]

        if kafka_attempt["task"]["checker"] is not None:
            attempt.task.checker = Checker(**kafka_attempt["task"]["checker"])
            attempt.task.checker.language = Language(
                **kafka_attempt["task"]["checker"]["language"]
            )

        return self._manager.start(attempt)

    def start(self):
        """Starts listener loop"""
        self.logging.info("Started")
        while self.running:
            msg = self.consumer.poll(0.5)

            if msg is None:
                continue
            self.logging.info("Polled message")
            if msg.error():
                continue

            payload = msg.value()

            if not isinstance(payload, bytes):
                continue

            attempt = json.loads(payload.decode("utf-8"))

            self.set_testing(attempt)

            tested_attempt = self.test_attempt(attempt)

            self.set_finished(attempt)

            if tested_attempt["language"] not in [1, 2] or tested_attempt["verdict"] != 0:
                self.sink_attempt(tested_attempt)
            self.detect_ai(tested_attempt)

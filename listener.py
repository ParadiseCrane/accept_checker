"""Contains Listener for database updates class"""

import os
import logging

from typing import Any
from quixstreams import Application
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


logging.getLogger("Listener")


class Listener:
    """Listens to database updates"""

    _manager_path = os.path.join(".", "manager.py")

    def __init__(self) -> None:
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

    def set_testing(self, attempt: dict[str, Any]) -> dict[str, Any]:
        return {"spec": attempt["spec"], "status": map_attempt_status("testing")}

    def set_finished(self, tested_attempt: dict[str, Any]) -> dict[str, Any]:
        return {"spec": tested_attempt["spec"], "status": map_attempt_status("finished")}

    def test_attempt(self, kafka_attempt: dict[str, Any]) -> dict[str, Any]:
        logging.info(f"Testing attempt `{kafka_attempt["spec"]}`")
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

    def detect_ai(self, tested_attempt: dict[str, Any]):
        if tested_attempt["language"] not in [1, 2]: # Python, Pypy
            return
        if tested_attempt["verdict"] != 0: # OK
            return
        tested_attempt.update({"detect_ai": True})

    async def start(self):
        """Starts listener loop"""

        app = Application(self._kafka_string, consumer_group="checker")

        input_topic = app.topic("attempt_checker")
        output_topic = app.topic("attempt_detect_ai")
        status_topic = app.topic("attempt_status")

        sdf = app.dataframe(input_topic)

        sdf.apply(self.set_testing).to_topic(status_topic)

        sdf_tested = sdf.apply(self.test_attempt)

        # TODO: is assignment needed
        _sdf2 = sdf_tested.apply(self.set_finished).to_topic(status_topic)

        sdf_tested = sdf_tested.update(self.detect_ai).to_topic(output_topic)

        app.run()


LISTENER = Listener()

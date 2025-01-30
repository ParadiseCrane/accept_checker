"""Contains Listener for database updates class"""

import os

from typing import Any
from quixstreams import Application
from utils.basic import map_attempt_status

from local_secrets import SECRETS_MANAGER
from settings import SETTINGS_MANAGER
# from manager import Manager


class Listener:
    """Listens to database updates"""

    _manager_path = os.path.join(".", "manager.py")

    def __init__(self) -> None:
        # self._manager = Manager()
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

    def set_finished(self, attempt: dict[str, Any]) -> dict[str, Any]:
        return {"spec": attempt["spec"], "status": map_attempt_status("finished")}

    def test_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        # TODO: Add logic
        return attempt

    def detect_ai(self, tested_attempt: dict[str, Any]):
        # TODO: Add logic
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

        sdf2 = sdf_tested.apply(self.set_finished).to_topic(status_topic)

        sdf_tested = sdf_tested.update(self.detect_ai).to_topic(output_topic)

        app.run()


LISTENER = Listener()

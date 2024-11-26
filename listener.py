"""Contains Listener for database updates class"""

import concurrent.futures as pool
import json
import os
import subprocess
import sys

from aiokafka import AIOKafkaConsumer

from local_secrets import SECRETS_MANAGER
from settings import SETTINGS_MANAGER


class Listener:
    """Listens to database updates"""

    def __init__(self, manager_path: str = os.path.join(".", "manager.py")) -> None:
        self._kafka_string = SECRETS_MANAGER.get_kafka_string()
        self.kafka_debug = SETTINGS_MANAGER.kafka_debug

        self._manager_path = manager_path
        self._current_dir = os.path.dirname(os.path.abspath(__file__))

        self.settings = SETTINGS_MANAGER.listener
        self.cpu_number = os.cpu_count() or 0
        self.max_workers = max(
            2,
            int(self.cpu_number * self.settings.cpu_utilization_fraction),
        )

    def submit_to_manager(
        self,
        attempt_spec: str,
        author_login: str,
        task_spec: str,
        organization_spec: str,
    ) -> None:
        """Submits attempt to Manager in separate process

        Args:
            attempt_spec (str): spec of attempt
            author_login (str): login of author
            task_spec (str): spec of task
            organization_spec (str): spec of organization

        """
        try:
            subprocess.run(
                [
                    "python",
                    self._manager_path,
                    attempt_spec,
                    author_login,
                    task_spec,
                    organization_spec,
                ],
                check=True,
            )

        except BaseException as exception:  # pylint:disable=W0718
            print("Listener error", f"Error when starting manager: {exception}")

    async def start(self):
        """Starts listener loop"""

        consumer = AIOKafkaConsumer(
            "attempt",
            bootstrap_servers=self._kafka_string,
            auto_commit_interval_ms=1000,
            auto_offset_reset="earliest",
            group_id="kafka_test",
        )

        await consumer.start()
        try:
            while True:
                with pool.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    async for attempt in consumer:
                        attempt = attempt.value.decode("utf-8")
                        attempt = json.loads(attempt)

                        attempt_spec = attempt["attempt"]
                        author_login = attempt["author"]
                        task_spec = attempt["task"]
                        organization_spec = attempt["organization"]

                        if self.kafka_debug:
                            print(
                                f"\nattempt: {attempt_spec}\n\tlogin: {author_login}\n\ttask: {task_spec}\n\torg: {organization_spec}"
                            )

                        executor.submit(
                            self.submit_to_manager,
                            attempt_spec,
                            author_login,
                            task_spec,
                            organization_spec,
                        )
        except KeyboardInterrupt:
            print("\nExit")
            sys.exit(0)
        finally:
            await consumer.stop()


LISTENER = Listener()

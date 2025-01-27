"""Contains Listener for database updates class"""

import concurrent.futures as pool
import json
import os
import subprocess
import sys
import time
from typing import Any, Callable

from aiokafka import AIOKafkaConsumer

from local_secrets import SECRETS_MANAGER
from settings import SETTINGS_MANAGER


class Listener:
    """Listens to database updates"""

    _manager_path = os.path.join(".", "manager.py")

    def __init__(self) -> None:
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

    @staticmethod
    def submit_to_manager(
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
                    Listener._manager_path,
                    attempt_spec,
                    author_login,
                    task_spec,
                    organization_spec,
                ],
                check=True,
                capture_output=True,
            )

        except BaseException as exception:  # pylint:disable=W0718
            print("Listener error", f"Error when starting manager: {exception}")

    def attempt_checked(self, attempt_spec):
        self.busy_cpu -= 1
        if self._debug:
            print(f"attempt {attempt_spec} checked!")

    def _get_attempt_spec_callback(self, attempt_spec: str) -> Callable[[Any], None]:
        return lambda _: self.attempt_checked(attempt_spec)

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
                if self.busy_cpu >= self.max_workers:
                    time.sleep(self.settings.sleep_timeout_seconds)
                    continue
                with pool.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    result = await consumer.getmany(
                        max_records=self.max_workers - self.busy_cpu, timeout_ms=10000
                    )
                    for _, attempts in result.items():
                        for attempt in attempts:
                            if attempt.value is None:
                                continue
                            attempt = attempt.value.decode("utf-8")
                            attempt = json.loads(attempt)

                            attempt_spec = attempt["attempt"]
                            author_login = attempt["author"]
                            task_spec = attempt["task"]
                            organization_spec = attempt["organization"]

                            if self._debug:
                                print(
                                    f"\nattempt: {attempt_spec}\n\tlogin: {author_login}\n\ttask: {task_spec}\n\torg: {organization_spec}"
                                )

                            self.busy_cpu += 1
                            future = executor.submit(
                                Listener.submit_to_manager,
                                attempt_spec,
                                author_login,
                                task_spec,
                                organization_spec,
                            )

                            future.add_done_callback(
                                self._get_attempt_spec_callback(attempt_spec)
                            )

        except KeyboardInterrupt:
            print("\nExit")
            sys.exit(0)
        finally:
            if consumer:
                await consumer.stop()


LISTENER = Listener()

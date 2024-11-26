"""Contains Listener for database updates class"""

import concurrent.futures as pool
import os
import subprocess
import sys

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
            )

        except BaseException as exception:  # pylint:disable=W0718
            print("Listener error", f"Error when starting manager: {exception}")

    async def start(self):
        """Starts listener loop"""

        # consumer = AIOKafkaConsumer(
        #     "attempt",
        #     bootstrap_servers=self._kafka_string,
        #     auto_commit_interval_ms=1000,
        #     auto_offset_reset="earliest",
        #     group_id="kafka_test",
        # )

        # await consumer.start()

        consumer = [
            {
                "organization": "vml",
                "attempt": "76ab9063-166b-4d76-8984-5d29a93f261b",
                "author": "AleksOleynik",
                "task": "431be734-39e6-4f58-aec7-61e67c8ee1b5",
                "taskType": 0,
                "taskCheckType": 0,
                "checker": None,
            }
        ]

        try:
            while True:
                with pool.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    # async for attempt in consumer:
                    #     attempt = attempt.value.decode("utf-8")
                    #     attempt = json.loads(attempt)
                    for attempt in consumer:
                        attempt_spec = attempt["attempt"]
                        author_login = attempt["author"]
                        task_spec = attempt["task"]
                        organization_spec = attempt["organization"]

                        if self._debug:
                            print(
                                f"\nattempt: {attempt_spec}\n\tlogin: {author_login}\n\ttask: {task_spec}\n\torg: {organization_spec}"
                            )

                        future = executor.submit(
                            Listener.submit_to_manager,
                            attempt_spec,
                            author_login,
                            task_spec,
                            organization_spec,
                        )

                        if self._debug:
                            future.add_done_callback(lambda _: print("Finished!"))

        except KeyboardInterrupt:
            print("\nExit")
            sys.exit(0)
        finally:
            # await consumer.stop()
            pass


LISTENER = Listener()

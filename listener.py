"""Contains Listener for database updates class"""

import subprocess
import sys

import os
import asyncio
import concurrent.futures as pool
from database import DATABASE
from settings import SETTINGS_MANAGER
from typing import List, Any

class Listener:
    """Listens to database updates"""

    async def _get_pending_items(self, limit: int = 10)-> List[Any]:
        collection = DATABASE.get_collection(self._pending_attempts_collection_name)

        item_dicts: Any = []
        async for queue_item in collection.aggregate(
            [
                {"$match": {"examined": None}},
                {"$limit": limit},
                {"$project": {"author": 1, "task": 1, "attempt": 1}},
            ]
        ):
            item_dicts.append(queue_item)

        await collection.update_many(
            {"attempt": {"$in": list(map(lambda item: item["attempt"], item_dicts))}},
            {"$set": {"examined": True}},
        )

        return item_dicts

    def __init__(self, manager_path: str = os.path.join(".", "manager.py")) -> None:
        self._manager_path = manager_path
        self._current_dir = os.path.dirname(os.path.abspath(__file__))
        self._pending_attempts_collection_name = "pending_task_attempt"

        self.settings = SETTINGS_MANAGER.listener
        self.cpu_number = os.cpu_count() or 0
        self.max_workers = max(
            2,
            int(self.cpu_number * self.settings.cpu_utilization_fraction),
        )

    def submit_to_manager(
        self, attempt_spec: str, author_login: str, task_spec: str
    ) -> None:
        """Submits attempt to Manager in separate process

        Args:
            attempt_spec (str): spec of attempt
            author_login (str): login of author
            task_spec (str): spec of task

        """
        try:
            subprocess.run(
                ["python", self._manager_path, attempt_spec, author_login, task_spec],
                check=True,
            )
        except BaseException as exception:  # pylint:disable=W0718
            print("Listener error", f"Error when starting manager: {exception}")

    async def start(self):
        """Starts listener loop"""

        try:
            with pool.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                while True:
                    try:
                        queue_items = await self._get_pending_items()
                        for queue_item in queue_items:
                            attempt_spec = queue_item["attempt"]
                            author_login = queue_item["author"]
                            task_spec = queue_item["task"]

                            executor.submit(
                                self.submit_to_manager,
                                attempt_spec,
                                author_login,
                                task_spec,
                            )

                    except BaseException as exception:  # pylint:disable=W0718
                        print(exception)

                    await asyncio.sleep(self.settings.sleep_timeout_seconds)
        except KeyboardInterrupt:
            print("\nExit")
            sys.exit(0)


LISTENER = Listener()

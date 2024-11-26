"""Contains Manager for running the checker class"""

import asyncio
import os
import sys
from math import floor
from typing import Any, Callable, Coroutine, Optional

from checker.custom_checker import CustomChecker
from checker.tests import TestsChecker
from checker.text import TextChecker
from database import Database
from models import Attempt, Language, PendingQueueItem, TaskTest
from settings import SETTINGS_MANAGER
from utils.basic import (
    create_program_folder,
    delete_folder,
    generate_tests_verdicts,
    group_values,
    map_attempt_status,
    map_verdict,
    prepare_test_groups,
    send_alert,
)


def _soft_run(func: Callable[..., Any]) -> Callable[..., Coroutine[Any, Any, Any]]:
    async def inner(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ):
        try:
            await func(
                self,
                attempt,
                author_login,
                task_spec,
                *args,
                **kwargs,
            )
        except BaseException as manager_exc:  # pylint: disable=W0718
            results = attempt.results
            await send_alert("ManagerError", f"{attempt.spec}\n{manager_exc}")
            # TODO: delete folder
            try:
                await self._save_results(  # pylint:disable=W0212:protected-access
                    attempt,
                    author_login,
                    task_spec,
                    generate_tests_verdicts("SE", len(results)),
                    [str(manager_exc)],
                )
            except BaseException as saving_exception:  # pylint: disable=W0718
                await send_alert(
                    "ManagerError (when saving results)",
                    f"{attempt.spec}\n{str(saving_exception)}",
                )

    return inner


class Manager:
    """Manages different checkers and task types"""

    async def _set_testing(
        self, attempt: Attempt, author_login: str, task_spec: str
    ) -> bool:
        status = map_attempt_status("testing")
        attempt_result, _ = await asyncio.gather(
            *[
                self._db.update_one(
                    "attempt", {"spec": attempt.spec}, {"$set": {"status": status}}
                ),
                self._db.update_one(
                    "user_task_status",
                    {"attempt": attempt.spec},
                    {"$set": {"status": status}},
                ),
            ]
        )

        is_testing_set = attempt_result.modified_count == 1

        if not is_testing_set:
            await self._save_results(
                attempt,
                author_login,
                task_spec,
                generate_tests_verdicts("NT", len(attempt.results)),
                ["Error in setting testing status"],
            )

        return is_testing_set

    async def _get_attempt_final_info(
        self,
        results: list[Attempt.Result],
        verdicts: list[int],
    ) -> tuple[int, int]:
        for idx, result in enumerate(results):
            results[idx].verdict = verdicts[idx]

        attempt_final_verdict = map_verdict("NT")
        attempt_final_verdict_test = 0

        for result in results:
            attempt_final_verdict = result.verdict
            if result.verdict != 0:
                break
            attempt_final_verdict_test += 1
        else:
            attempt_final_verdict_test -= 1
        return attempt_final_verdict, attempt_final_verdict_test

    async def _save_attempt_results(
        self,
        attempt_spec: str,
        results: list[Attempt.Result],
        attempt_final_verdict: int,
        attempt_final_verdict_test: int,
        logs: list[str],
    ):
        results_dict = [result.to_dict() for result in results]
        await self._db.update_one(
            "attempt",
            {"spec": attempt_spec},
            {
                "$set": {
                    "status": map_attempt_status("finished"),
                    "verdict": attempt_final_verdict,
                    "verdictTest": attempt_final_verdict_test,
                    "results": results_dict,
                    "logs": logs,
                }
            },
        )

    async def _save_task_results(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        verdicts: list[int],
        attempt_final_verdict: int,
        attempt_final_verdict_test: int,
    ):
        ok_verdict_spec = map_verdict("OK")
        passed_tests = len(
            list(filter(lambda verdict: verdict == ok_verdict_spec, verdicts))
        )
        percent_tests = floor(passed_tests / len(verdicts) * 100)

        current_attempt = {
            "attempt": attempt.spec,
            "date": attempt.date,
            "passedTests": passed_tests,
            "percentTests": percent_tests,
            "verdict": attempt_final_verdict,
            "verdictTest": attempt_final_verdict_test,
        }

        user_task_result_collection = self._db.get_collection("user_task_result")

        user_task_result_dict = await user_task_result_collection.find_one(
            {"task": task_spec, "user": author_login}
        )

        if not user_task_result_dict or len(user_task_result_dict["bests"]) == 0:
            best_attempt = None
        else:
            best_attempt = user_task_result_dict["bests"][-1]

        new_best_attempt = None
        if best_attempt and (
            best_attempt["verdict"] == attempt_final_verdict == ok_verdict_spec
            or best_attempt["percentTests"] > percent_tests
        ):
            new_best_attempt = best_attempt
            new_best_attempt["date"] = attempt.date
        else:
            new_best_attempt = current_attempt

        database_actions: Any = []

        if (not best_attempt or best_attempt["verdict"] != 0) and new_best_attempt[
            "verdict"
        ] == 0:
            database_actions.append(
                self._db.update_one(
                    "rating", {"user": author_login}, {"$inc": {"score": 1}}, True
                )
            )

        if not user_task_result_dict:
            database_actions.append(
                user_task_result_collection.insert_one(
                    {
                        "task": task_spec,
                        "user": author_login,
                        "results": [current_attempt],
                        "bests": [new_best_attempt],
                    }
                )
            )

        else:
            database_actions.append(
                user_task_result_collection.update_one(
                    {"task": task_spec, "user": author_login},
                    {"$push": {"results": current_attempt, "bests": new_best_attempt}},
                )
            )

        await asyncio.gather(*database_actions)

    async def _save_results(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        verdicts: list[int],
        logs: list[str],
    ):
        (
            attempt_final_verdict,
            attempt_final_verdict_test,
        ) = await self._get_attempt_final_info(attempt.results, verdicts)

        await asyncio.gather(
            *[
                self._db.delete_one("pending_task_attempt", {"attempt": attempt.spec}),
                self._save_attempt_results(
                    attempt.spec,
                    attempt.results,
                    attempt_final_verdict,
                    attempt_final_verdict_test,
                    logs,
                ),
                self._save_task_results(
                    attempt,
                    author_login,
                    task_spec,
                    verdicts,
                    attempt_final_verdict,
                    attempt_final_verdict_test,
                ),
                self._db.update_one(
                    "user_task_status",
                    {"attempt": attempt.spec},
                    {"$set": {"status": map_attempt_status("finished")}},
                ),
            ]
        )

    def _get_constraints(
        self, attempt: Attempt
    ) -> tuple[Optional[float], Optional[float]]:
        constraints = attempt.constraints
        return constraints.time, constraints.memory

    def _get_offsets(self, language_dict: dict[str, Any]) -> tuple[float, float, float]:
        return (
            language_dict["compileOffset"],
            language_dict["runOffset"],
            language_dict["memOffset"],
        )

    async def _handle_code_task(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        task_tests: list[TaskTest],
        test_groups: list[int],
        queue_item: PendingQueueItem,
    ):
        check_type = queue_item.task_check_type

        grouped_tests: list[list[TaskTest]] = group_values(task_tests, test_groups)

        await self._task_check_type_handler[check_type](
            attempt, author_login, task_spec, grouped_tests, queue_item
        )

    @_soft_run
    async def _handle_text_task(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        task_tests: list[TaskTest],
        test_groups: list[int],
        _queue_item: PendingQueueItem,
    ):
        is_set_testing = await self._set_testing(attempt, author_login, task_spec)
        if not is_set_testing:
            return

        user_answers: list[str] = attempt.text_answers

        correct_answers: list[str] = [task_test.output_data for task_test in task_tests]

        text_checker = self.text_checker_class()
        verdicts, logs = await text_checker.start(
            user_answers, correct_answers, test_groups
        )
        await self._save_results(attempt, author_login, task_spec, verdicts, logs)

    @_soft_run
    async def _handle_tests_checker(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        grouped_tests: list[list[TaskTest]],
        _queue_item: PendingQueueItem,
    ):
        is_set = await self._set_testing(attempt, author_login, task_spec)
        if not is_set:
            return

        language_dict = await self._db.find_one("language", {"spec": attempt.language})
        language = Language(language_dict)

        folder_path = create_program_folder(attempt.spec)

        tests_checker = self.tests_checker_class()

        verdicts, logs = await tests_checker.start(
            attempt,
            grouped_tests,
            folder_path,
            language,
        )

        delete_folder(folder_path)

        await self._save_results(attempt, author_login, task_spec, verdicts, logs)

    @_soft_run
    async def _handle_custom_checker(
        self,
        attempt: Attempt,
        author_login: str,
        task_spec: str,
        grouped_tests: list[list[TaskTest]],
        queue_item: PendingQueueItem,
    ):
        is_set = await self._set_testing(attempt, author_login, task_spec)
        if not is_set:
            return

        if not queue_item.checker:
            await self._save_results(
                attempt,
                author_login,
                task_spec,
                generate_tests_verdicts("NT", len(attempt.results)),
                ["Error in setting testing status"],
            )
            return

        program_language_dict, checker_language_dict = await asyncio.gather(
            *[
                self._db.find_one("language", {"spec": attempt.language}),
                self._db.find_one("language", {"spec": queue_item.checker.language}),
            ]
        )
        program_language = Language(program_language_dict)
        checker_language = Language(checker_language_dict)

        folder_path = create_program_folder(attempt.spec)

        custom_checker_ = self.custom_checker_class()

        verdicts, logs = await custom_checker_.start(
            queue_item.checker,
            attempt,
            grouped_tests,
            folder_path,
            program_language,
            checker_language,
        )

        delete_folder(folder_path)

        await self._save_results(attempt, author_login, task_spec, verdicts, logs)

    def __init__(self, organization: str) -> None:
        self._db = Database(organization)  # org

        self._current_dir = os.path.dirname(os.path.abspath(__file__))
        self._task_type_handler = {
            0: self._handle_code_task,
            1: self._handle_text_task,
        }

        self._task_check_type_handler = {
            0: self._handle_tests_checker,
            1: self._handle_custom_checker,
        }

        self.text_checker_class = TextChecker
        self.tests_checker_class = TestsChecker
        self.custom_checker_class = CustomChecker

        self.settings = SETTINGS_MANAGER.manager

    async def start(
        self,
        attempt_spec: str,
        author_login: str,
        task_spec: str,
    ):
        """Starts Manager for given pending item

        Args:
            attempt_spec (str): attempt spec
            author_login (str): author login
            task_spec (str): task spec
            organization_spec (str): organization spec
        """

        attempt_dict, queue_item_dict, task_dict = await asyncio.gather(
            *[
                self._db.find_one("attempt", {"spec": attempt_spec}),
                self._db.find_one(
                    "pending_task_attempt",
                    {"attempt": attempt_spec},
                    {"taskType": 1, "taskCheckType": 1, "checker": 1},
                ),
                self._db.find_one(
                    "task",
                    {"spec": task_spec},
                    {"test_groups": 1, "tests": 1},
                ),
            ]
        )

        queue_item = PendingQueueItem(queue_item_dict)
        attempt = Attempt(attempt_dict)

        test_groups: list[int] = prepare_test_groups(
            task_dict["test_groups"], len(task_dict["tests"])
        )

        task_tests_specs = [result.test for result in attempt.results]
        task_tests_map: dict[str, TaskTest] = dict()  # spec : TaskTest
        for task_test_dict in await self._db.find(
            "task_test", {"spec": {"$in": task_tests_specs}}
        ):
            task_tests_map[task_test_dict["spec"]] = TaskTest(task_test_dict)

        task_tests: list[TaskTest] = [
            task_tests_map[result.test] for result in attempt.results
        ]

        task_type = int(queue_item_dict["taskType"])

        await self._task_type_handler[task_type](
            attempt,
            author_login,
            task_spec,
            task_tests,
            test_groups,
            queue_item,
        )


if __name__ == "__main__":
    (
        *_,
        attempt_spec_arg,
        author_login_arg,
        task_spec_arg,
        organization_spec_arg,
    ) = sys.argv

    asyncio.run(
        Manager(organization_spec_arg).start(
            attempt_spec_arg, author_login_arg, task_spec_arg
        )
    )

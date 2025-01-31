"""Contains Manager for running the checker class"""

import os
from typing import Any, Callable, Optional
import logging
from dataclasses import asdict

from checker.custom_checker import CustomChecker
from checker.tests import TestsChecker
from checker.text import TextChecker
from models import Attempt, ProcessedAttempt, TaskTest, Result
from settings import SETTINGS_MANAGER
from utils.basic import (
    create_program_folder,
    delete_folder,
    generate_tests_verdicts,
    group_values,
    map_verdict,
    prepare_test_groups,
    send_alert,
)

logger = logging.getLogger("Manager")
logger.setLevel(logging.INFO)


def _soft_run(func: Callable[..., Any]) -> Callable[..., ProcessedAttempt]:
    def inner(
        self,
        attempt: Attempt,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> ProcessedAttempt:
        try:
            return func(
                self,
                attempt,
                *args,
                **kwargs,
            )
        except BaseException as manager_exc:  # pylint: disable=W0718
            send_alert("ManagerError", f"{attempt.spec}\n{manager_exc}")
            # TODO: delete folder
            try:
                return self._save_results(  # pylint:disable=W0212:protected-access
                    attempt,
                    generate_tests_verdicts("SE", len(attempt.task.tests)),
                    [str(manager_exc)],
                )
            except BaseException as saving_exception:  # pylint: disable=W0718
                send_alert(
                    "ManagerError (when saving results)",
                    f"{attempt.spec}\n{str(saving_exception)}",
                )
                # TODO: check return
                raise NotImplementedError

    return inner  # type: ignore


class Manager:
    """Manages different checkers and task types"""

    def __init__(self) -> None:
        self._current_dir = os.path.dirname(os.path.abspath(__file__))
        self._task_type_handler: dict[int, Callable[..., ProcessedAttempt]] = {
            0: self._handle_code_task,
            1: self._handle_text_task,
        }

        self._task_check_type_handler: dict[int, Callable[..., ProcessedAttempt]] = {
            0: self._handle_tests_checker,
            1: self._handle_custom_checker,
        }

        self.text_checker_class = TextChecker
        self.tests_checker_class = TestsChecker
        self.custom_checker_class = CustomChecker

        self.settings = SETTINGS_MANAGER.manager

    def _get_attempt_final_info(
        self,
        results: list[Result],
        verdicts: list[int],
    ) -> tuple[list[Result], int, int]:
        for idx, result in enumerate(results):
            results[idx].verdict = verdicts[idx]

        attempt_final_verdict = map_verdict("NT")
        attempt_final_verdict_test = 0

        for idx in range(len(results)):
            attempt_final_verdict = results[idx].verdict
            if results[idx].verdict != map_verdict("OK"):
                break
            attempt_final_verdict_test += 1
        else:
            attempt_final_verdict_test -= 1
        return results, attempt_final_verdict, attempt_final_verdict_test

    def _save_results(
        self,
        attempt: Attempt,
        verdicts: list[int],
        logs: list[str],
    ) -> ProcessedAttempt:
        results = [Result(test=test.spec, verdict=map_verdict("NT")) for test in attempt.task.tests]
        (
            results,
            verdict,
            verdict_test,
        ) = self._get_attempt_final_info(results, verdicts)

        # TODO: change best result

        return ProcessedAttempt(
            spec=attempt.spec,
            author=attempt.author,
            date=attempt.date,
            language=attempt.language.spec,
            organization=attempt.organization,
            programText=attempt.programText,
            results=results,
            verdict=verdict,
            verdictTest=verdict_test,
            logs=logs,
        )

    def _get_constraints(
        self, attempt: Attempt
    ) -> tuple[Optional[float], Optional[float]]:
        constraints = attempt.task.constraints
        return constraints.time, constraints.memory

    def _get_offsets(self, language_dict: dict[str, Any]) -> tuple[float, float, float]:
        return (
            language_dict["compileOffset"],
            language_dict["runOffset"],
            language_dict["memOffset"],
        )

    @_soft_run
    def _handle_code_task(
        self,
        attempt: Attempt,
        test_groups: list[int],
    ) -> ProcessedAttempt:
        check_type = attempt.task.checkType

        grouped_tests: list[list[TaskTest]] = group_values(
            attempt.task.tests, test_groups
        )

        return self._task_check_type_handler[check_type](attempt, grouped_tests)

    @_soft_run
    def _handle_text_task(
        self,
        attempt: Attempt,
        test_groups: list[int],
    ) -> ProcessedAttempt:
        user_answers: list[str] = attempt.textAnswers

        correct_answers: list[str] = [
            task_test.outputData for task_test in attempt.task.tests
        ]

        text_checker = self.text_checker_class()
        verdicts, logs = text_checker.start(user_answers, correct_answers, test_groups)
        return self._save_results(attempt, verdicts, logs)

    @_soft_run
    def _handle_tests_checker(
        self,
        attempt: Attempt,
        grouped_tests: list[list[TaskTest]],
    ) -> ProcessedAttempt:
        language = attempt.language

        folder_path = create_program_folder(attempt.spec)

        tests_checker = self.tests_checker_class()

        verdicts, logs = tests_checker.start(
            attempt,
            grouped_tests,
            folder_path,
            language,
        )

        delete_folder(folder_path)

        return self._save_results(attempt, verdicts, logs)

    @_soft_run
    def _handle_custom_checker(
        self,
        attempt: Attempt,
        grouped_tests: list[list[TaskTest]],
    ) -> ProcessedAttempt:
        if not attempt.task.checker:
            return self._save_results(
                attempt,
                generate_tests_verdicts("NT", len(attempt.task.tests)),
                ["Error in setting testing status"],
            )

        program_language = attempt.language
        checker_language = attempt.task.checker.language

        folder_path = create_program_folder(attempt.spec)

        custom_checker_ = self.custom_checker_class()

        verdicts, logs = custom_checker_.start(
            attempt.task.checker,
            attempt,
            grouped_tests,
            folder_path,
            program_language,
            checker_language,
        )

        delete_folder(folder_path)

        return self._save_results(attempt, verdicts, logs)

    def start(
        self,
        attempt: Attempt,
    ) -> dict[str, Any]:
        """Starts Manager for given pending item

        Args:
            attempt_spec (Attempt): attempt with all needed information
        """

        task = attempt.task

        test_groups: list[int] = prepare_test_groups(task.test_groups, len(task.tests))

        task_tests_map: dict[str, TaskTest] = dict()  # spec : TaskTest
        for test in task.tests:
            task_tests_map[test.spec] = test

        logger.info(f"Testing attempt `{attempt.spec}`")

        result = self._task_type_handler[task.taskType](
            attempt,
            test_groups,
        )

        return asdict(result)

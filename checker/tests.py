"""Contains Tests Checker class"""

from typing import Tuple, List
from checker.basic import CodeChecker
from program_languages.utils import get_language_class
from custom_exceptions import (
    CompilationErrorException,
)
from models import Attempt, Language, TaskTest
from utils.basic import generate_program_name, generate_tests_verdicts


class TestsChecker(CodeChecker):
    """Provides evaluation for simple tests tasks"""

    async def start(  # pylint:disable=W0221:arguments-differ
        self,
        attempt: Attempt,
        task_tests: List[TaskTest],
        folder_path: str,
        language: Language,
    ) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:
            attempt (Attempt): attempt model
            task_tests (List[TaskTest]): tests of task,
            folder_path (str): path to the testing folder
            language (Language): Language model

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        try:
            language_class = get_language_class(language.short_name)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(task_tests)),
                [
                    f"Attempt {attempt.spec}",
                    f"No language with short name '{language.short_name}'",
                    str(exc),
                ],
            )

        program_name = generate_program_name(attempt)

        try:
            self.write_program_text(
                folder_path, program_name, attempt.program_text, language_class
            )
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(task_tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path, program_name, language_class, language.compile_offset
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CE", len(task_tests)), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(task_tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        verdicts = self.run_tests(
            folder_path, program_name, attempt, task_tests, language, language_class
        )

        return verdicts, []

"""Contains Tests Checker class"""

from typing import Tuple, List
from checker.basic import CodeChecker
from program_languages.utils import get_language_class
from custom_exceptions import (
    CompilationErrorException,
)
from models import Attempt, Language

from utils.basic import generate_program_name, generate_tests_verdicts


class TestsChecker(CodeChecker):
    """Provides evaluation for simple tests tasks"""

    async def start(  # pylint:disable=W0221:arguments-differ
        self,
        attempt: Attempt,
        folder_path: str,
        language: Language,
    ) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:
            attempt (Attempt): attempt model
            folder_path (str): path to the testing folder
            language (Language): Language model

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        tests: List[Attempt.Result.Test] = [result.test for result in attempt.results]

        try:
            language_class = get_language_class(language.short_name)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
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
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path, program_name, language_class, language.compile_offset
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CE", len(tests)), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        verdicts = self.run_tests(
            folder_path, program_name, attempt, language, language_class
        )

        return verdicts, []

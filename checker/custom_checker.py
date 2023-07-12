"""Contains Custom checker class"""

from typing import Optional, List, Tuple
from checker.basic import CodeChecker
from custom_process import CustomProcess
from program_languages.utils import get_language_class
from models import Attempt, Language, PendingQueueItem
from utils.basic import (
    VerdictType,
    generate_program_name,
    generate_tests_verdicts,
    map_verdict,
)
from custom_exceptions import CompilationErrorException


class CustomChecker(CodeChecker):
    """Custom task checker class"""

    def __init__(self) -> None:
        super().__init__()
        self.checker_process: Optional[CustomProcess] = None

        self._checker_ok_output = "1"

    def _check_test(
        self,
        attempt: Attempt,
        index: int,
        verdict: Optional[VerdictType],
        program_output: Optional[str],
    ) -> int:
        if verdict is not None:
            return map_verdict(verdict)

        if self.checker_process is None:
            return map_verdict("SE")

        if program_output is None:
            return map_verdict("WA")

        try:
            checker_output = self.checker_process.run(
                f"{attempt.results[index].test.input_data}\n{program_output.strip()}",
            ).strip()

            if checker_output == self._checker_ok_output:
                return map_verdict("OK")
        except BaseException:  # pylint:disable=W0718
            return map_verdict("SE")

        return map_verdict("WA")

    async def start(  # pylint:disable=W0221
        self,
        checker: PendingQueueItem.Checker,
        attempt: Attempt,
        folder_path: str,
        program_language: Language,
        checker_language: Language,
    ) -> Tuple[List[int], List[str]]:
        tests: List[Attempt.Result.Test] = [result.test for result in attempt.results]

        try:
            program_language_class = get_language_class(program_language.short_name)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [
                    f"Attempt {attempt.spec}",
                    f"No language with short name '{program_language.short_name}'",
                    str(exc),
                ],
            )
        try:
            checker_language_class = get_language_class(checker_language.short_name)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [
                    f"Attempt {attempt.spec}",
                    f"No language with short name '{checker_language.short_name}'",
                    str(exc),
                ],
            )

        checker_name = f"{generate_program_name(attempt)}_ch"

        try:
            self.write_program_text(
                folder_path, checker_name, checker.source_code, checker_language_class
            )
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path,
                checker_name,
                checker_language_class,
                checker_language.compile_offset,
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CH", len(tests)), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        self.checker_process = CustomProcess(
            checker_language_class.get_cmd_run(folder_path, checker_name),
            checker_language_class.get_memory_usage,
        )

        program_name = generate_program_name(attempt)

        try:
            self.write_program_text(
                folder_path, program_name, attempt.program_text, program_language_class
            )
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path,
                program_name,
                program_language_class,
                program_language.compile_offset,
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CE", len(tests)), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", len(tests)),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        verdicts = self.run_tests(
            folder_path, program_name, attempt, program_language, program_language_class
        )

        return verdicts, []

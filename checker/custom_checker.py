"""Contains Custom checker class"""

from typing import Optional

from checker.basic import CodeChecker
from custom_exceptions import CompilationErrorException
from custom_process import CustomProcess
from models import Attempt, Language, TaskTest, Checker
from program_languages.utils import get_language_class
from utils.basic import (
    VerdictType,
    generate_program_name,
    generate_tests_verdicts,
    map_verdict,
)


class CustomChecker(CodeChecker):
    """Custom task checker class"""

    def __init__(self) -> None:
        super().__init__()
        self.checker_process: Optional[CustomProcess] = None

        self._checker_ok_output = "1"

    def _check_test(
        self,
        task_tests: list[TaskTest],
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
                f"{task_tests[index].inputData}\n{program_output.strip()}",
            ).strip()

            if checker_output == self._checker_ok_output:
                return map_verdict("OK")
        except BaseException:  # pylint:disable=W0718
            return map_verdict("SE")

        return map_verdict("WA")

    def start(  # pylint:disable=W0221
        self,
        checker: Checker,
        attempt: Attempt,
        grouped_tests: list[list[TaskTest]],
        folder_path: str,
        program_language: Language,
        checker_language: Language,
    ) -> tuple[list[int], list[str]]:
        """Starts checker

        Args:
            checker (BasicTaskInfo.Checker): program checker
            attempt (Attempt): user attempt
            grouped_tests (list[list[TaskTest]]): grouped task tests
            folder_path (str): path to the testing folder
            program_language (Language): Language model
            checker_language (Language): checker Language model

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        tests_number = sum(map(len, grouped_tests))

        try:
            program_language_class = get_language_class(program_language.shortName)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [
                    f"Attempt {attempt.spec}",
                    f"No language with short name '{program_language.shortName}'",
                    str(exc),
                ],
            )
        try:
            checker_language_class = get_language_class(checker_language.shortName)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [
                    f"Attempt {attempt.spec}",
                    f"No language with short name '{checker_language.shortName}'",
                    str(exc),
                ],
            )

        checker_name = f"{generate_program_name(attempt)}_ch"

        try:
            self.write_program_text(
                folder_path, checker_name, checker.sourceCode, checker_language_class
            )
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path,
                checker_name,
                checker_language_class,
                checker_language.compileOffset,
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CH", tests_number), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        self.checker_process = CustomProcess(
            checker_language_class.get_cmd_run(folder_path, checker_name),
            checker_language_class.get_memory_usage,
            compilation=False,
        )

        program_name = generate_program_name(attempt)

        try:
            self.write_program_text(
                folder_path, program_name, attempt.programText, program_language_class
            )
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path,
                program_name,
                program_language_class,
                program_language.compileOffset,
            )
        except CompilationErrorException:
            return (generate_tests_verdicts("CE", tests_number), [])
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        ok_verdict_spec = map_verdict("OK")

        verdicts = []
        all_correct = True
        for tests_group in grouped_tests:
            if not all_correct:
                verdicts += generate_tests_verdicts("NT", len(tests_group))
                continue

            group_verdicts = self.run_tests(
                folder_path,
                program_name,
                attempt,
                tests_group,
                program_language,
                program_language_class,
            )

            if all_correct:
                for verdict in group_verdicts:
                    if verdict != ok_verdict_spec:
                        all_correct = False
                        break

            verdicts += group_verdicts

        return verdicts, []

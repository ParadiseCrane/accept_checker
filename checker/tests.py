"""Contains Tests Checker class"""

from typing import List, Tuple

from checker.basic import CodeChecker
from custom_exceptions import CompilationErrorException
from models import Attempt, Language, TaskTest
from program_languages.utils import get_language_class
from utils.basic import generate_program_name, generate_tests_verdicts, map_verdict


class TestsChecker(CodeChecker):
    """Provides evaluation for simple tests tasks"""

    async def start(  # pylint:disable=W0221:arguments-differ
        self,
        attempt: Attempt,
        grouped_tests: List[List[TaskTest]],
        folder_path: str,
        language: Language,
    ) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:
            attempt (Attempt): attempt model
            grouped_tests (List[List[TaskTest]]): grouped task tests
            folder_path (str): path to the testing folder
            language (Language): Language model

        Returns:
            tuple[list[int], list[str]]: (verdicts, logs)
        """

        tests_number = sum(map(len, grouped_tests))

        try:
            language_class = get_language_class(language.short_name)
        except BaseException as exc:  # pylint: disable=W0718
            return (
                generate_tests_verdicts("SE", tests_number),
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
                generate_tests_verdicts("SE", tests_number),
                [f"Attempt {attempt.spec}", str(exc)],
            )

        try:
            self.compile_program(
                folder_path, program_name, language_class, language.compile_offset
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
                language,
                language_class,
            )

            if all_correct:
                for verdict in group_verdicts:
                    if verdict != ok_verdict_spec:
                        all_correct = False
                        break

            verdicts += group_verdicts

        return verdicts, []

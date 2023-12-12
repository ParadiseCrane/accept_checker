"""Contains Checker abstract class"""

import concurrent.futures as pool
import os
from itertools import zip_longest
from typing import Any, List, Optional, Tuple

from custom_exceptions import (
    CompilationErrorException,
    MemoryLimitException,
    RuntimeErrorException,
    ServerErrorException,
    TimeLimitException,
)
from custom_process import CustomProcess
from models import Attempt, Language, TaskTest
from program_languages.basic import ProgramLanguage
from utils.basic import VerdictType, generate_tests_verdicts, map_verdict


class Checker:
    """Basic checker abstract class"""

    def _compare_strings(self, test_string: str, answer_string: str) -> bool:
        """Compares two strings

        Args:
            test_string (str): first string
            answer_string (str): second string

        Returns:
            bool: are string equal
        """
        test_strings = map(lambda x: x.strip(), test_string.strip().split("\n"))
        answer_strings = map(lambda x: x.strip(), answer_string.strip().split("\n"))
        for test, answer in zip_longest(test_strings, answer_strings):
            if test != answer:
                return False
        return True

    async def start(self) -> Tuple[List[int], List[str]]:
        """Starts checker

        Args:


        Returns:
            tuple[list[int], list[str]]: (results, logs)
        """
        raise NotImplementedError


class CodeChecker(Checker):
    """Code checker basic class"""

    async def start(self) -> Tuple[List[int], List[str]]:
        raise NotImplementedError

    def write_program_text(
        self,
        folder_path: str,
        program_name: str,
        program_text: str,
        language: ProgramLanguage,
    ):
        """Writes users's code to the file

        Args:
            folder_path (str): path to the testing folder
            program_name (str): name of the program
            program_text (str): user's code
            language (Language): language class
        """

        program_path = os.path.abspath(
            os.path.join(
                folder_path,
                f"{program_name}.{language.get_compile_extension()}",
            )
        )

        with open(
            program_path,
            "w",
            encoding="utf8",
        ) as file:
            file.write(program_text)

    def compile_program(
        self,
        folder_path: str,
        program_name: str,
        language_class: ProgramLanguage,
        compile_offset: float,
    ):
        """Compiles the given program

        Args:
            folder_path (str): path to the testing folder
            program_name (str): name of the program
            language_class (ProgramLanguage): language class
            compile_offset (float): compilation offset in seconds
        """

        process = CustomProcess(
            language_class.get_cmd_compile(folder_path, program_name),
            language_class.get_memory_usage,
            compilation=True
        )

        try:
            process.run(time_offset=compile_offset)
        except RuntimeErrorException as exc:
            raise CompilationErrorException from exc
        except TimeLimitException as exc:
            raise CompilationErrorException from exc
        except MemoryLimitException as exc:
            raise CompilationErrorException from exc

    def _run_test(
        self,
        process: CustomProcess,
        index: int,
        attempt: Attempt,
        task_tests: List[TaskTest],
        language: Language,
    ) -> Tuple[int, Optional[VerdictType], Optional[str]]:
        verdict = None
        result = None
        try:
            result = process.run(
                input_data=task_tests[index].input_data,
                time_limit=attempt.constraints.time,
                time_offset=language.run_offset,
                memory_offset=language.mem_offset,
                memory_limit=attempt.constraints.memory << 20,
            )

        except TimeLimitException:
            verdict = "TL"
        except MemoryLimitException:
            verdict = "ML"
        except RuntimeErrorException:
            verdict = "RE"
        except ServerErrorException:
            verdict = "SE"
        except BaseException:  # pylint:disable=W0718
            verdict = "NT"

        return index, verdict, result

    def _check_test(
        self,
        task_tests: List[TaskTest],
        index: int,
        verdict: Optional[VerdictType],
        program_output: Optional[str],
    ) -> int:
        if verdict is not None:
            return map_verdict(verdict)

        if program_output is None:
            return map_verdict("WA")

        if self._compare_strings(program_output, task_tests[index].output_data):
            return map_verdict("OK")
        return map_verdict("WA")

    def _process_test(
        self,
        process: CustomProcess,
        index: int,
        attempt: Attempt,
        task_tests: List[TaskTest],
        language: Language,
    ) -> Tuple[int, int]:
        index, verdict, result = self._run_test(
            process, index, attempt, task_tests, language
        )
        return index, self._check_test(task_tests, index, verdict, result)

    def run_tests(
        self,
        folder_path: str,
        program_name: str,
        attempt: Attempt,
        task_tests: List[TaskTest],
        language: Language,
        language_class: ProgramLanguage,
    ) -> List[int]:
        """Runs tests for the given program

        Args:
            folder_path (str): path to the testing folder
            program_name (str): name of the program
            attempt (Attempt): user's attempt
            task_tests (List[TaskTest]): tests of task
            language (Language): language of the attempt
            language_class (ProgramLanguage): language class

        Returns:
            list[int]: verdicts
        """
        verdicts = generate_tests_verdicts("NT", len(task_tests))

        with pool.ThreadPoolExecutor(max_workers=5) as executor:
            processes = [
                CustomProcess(
                    language_class.get_cmd_run(folder_path, program_name),
                    language_class.get_memory_usage,
                    compilation=False
                )
                for _ in range(len(task_tests))
            ]

            pool_processes: List[Any] = []
            for index, process in enumerate(processes):
                pool_processes.append(
                    executor.submit(
                        self._process_test,
                        process,
                        index,
                        attempt,
                        task_tests,
                        language,
                    )
                )

            for process in pool.as_completed(pool_processes):
                try:
                    idx, verdict = process.result()
                    verdicts[idx] = verdict
                except BaseException:  # pylint:disable=W0718
                    pass
        return verdicts

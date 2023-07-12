"""Contains Tuner class"""

import shutil
import concurrent.futures as pool
from typing import Tuple, Callable, List, Any
import os
import subprocess
from datetime import datetime
import time
import psutil
import asyncio
from database import DATABASE
from date import DATE_TIME_INFO
from program_languages.basic import ProgramLanguage
from program_languages.utils import get_language_class
from models import Language
from settings import SETTINGS_MANAGER
from utils.basic import send_alert, kill_process_tree
from utils.soft_mkdir import soft_mkdir


class Tuner:
    """Tuner class"""

    def _write_program(self, code: str, language: ProgramLanguage) -> str:
        file_name = f"test_{int(datetime.utcnow().timestamp()*10**6)}"
        program_path = os.path.abspath(
            os.path.join(
                self.folder_path,
                f"{file_name}.{language.get_compile_extension()}",
            )
        )

        with open(
            program_path,
            "w",
            encoding="utf8",
        ) as file:
            file.write(code)

        return file_name

    def _clean_folder(self):
        for filename in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except BaseException:  # pylint:disable=W0718
                continue

    def _time_test(self, process: psutil.Popen, _: ProgramLanguage) -> float:
        cpu_time_usage = 0
        try:
            while process.is_running():
                cpu_time_usage = sum(process.cpu_times()[:-1])  # type: ignore
                time.sleep(self.test_sleep_seconds)
        except BaseException:  # pylint:disable=W0718
            pass
        return cpu_time_usage + self.test_sleep_seconds

    def _mem_test(
        self, process: psutil.Popen, language_class: ProgramLanguage
    ) -> float:
        memory_usage = 0
        total_sleep = 0

        try:
            while process.is_running():
                memory_usage = max(
                    memory_usage, language_class.get_memory_usage(process.memory_info())
                )
                if total_sleep >= self.mem_time_limit_seconds:
                    break
                total_sleep += self.test_sleep_seconds
                time.sleep(self.test_sleep_seconds)
        except BaseException:  # pylint:disable=W0718
            pass
        kill_process_tree(process.pid)

        return memory_usage

    def _run_cmd_test(
        self,
        cmd: List[str],
        test_function: Callable[[psutil.Popen, ProgramLanguage], float],
        language_class: ProgramLanguage,
    ) -> float:
        def run_test() -> float:
            process = psutil.Popen(
                cmd,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf8",
            )

            with pool.ThreadPoolExecutor(max_workers=2) as executor:
                info = executor.submit(test_function, process, language_class)
                executor.submit(process.wait)

            info_result = info.result()
            kill_process_tree(process.pid)

            return info_result

        test_runs: List[float] = []
        for _ in range(self.test_runs_count):
            test_runs.append(run_test())

        max_value = max(test_runs)
        test_runs.remove(max_value)
        return max(test_runs)  # takes the second max

    def _run_test(
        self,
        source_code: str,
        test_function: Callable[[psutil.Popen, ProgramLanguage], float],
        language_class: ProgramLanguage,
    ) -> Tuple[Any, Any]:
        file_name = self._write_program(source_code, language_class)

        compile_result = self._run_cmd_test(
            language_class.get_cmd_compile(self.folder_path, file_name),
            test_function,
            language_class,
        )

        run_result = self._run_cmd_test(
            language_class.get_cmd_run(self.folder_path, file_name),
            test_function,
            language_class,
        )

        self._clean_folder()

        return compile_result, run_result

    def _tune_language(self, language: Language) -> Tuple[float, float, int]:
        language_class: ProgramLanguage = get_language_class(language.short_name)

        time_offset_code, mem_offset_code = language_class.get_offset_codes()
        compile_offset_seconds, run_offset_seconds = self._run_test(
            time_offset_code, self._time_test, language_class
        )
        _, run_memory_offset_bytes = self._run_test(
            mem_offset_code, self._mem_test, language_class
        )

        return compile_offset_seconds, run_offset_seconds, run_memory_offset_bytes

    def __init__(self):
        self.test_sleep_seconds = 0.001
        self.mem_time_limit_seconds = 3
        self.test_runs_count = SETTINGS_MANAGER.tuner.test_runs_count
        self.folder_path = os.path.join(".", SETTINGS_MANAGER.tuner.tests_folder)
        soft_mkdir(self.folder_path)

    async def start(self):
        """Starts tuner"""
        language_dicts = await DATABASE.find("language")

        languages = [Language(language_dict) for language_dict in language_dicts]

        for language in languages:
            try:
                (
                    compile_offset_seconds,
                    run_offset_seconds,
                    memory_offset_bytes,
                ) = self._tune_language(language)

                await DATABASE.update_one(
                    "language",
                    {"spec": language.spec},
                    {
                        "$set": {
                            "compileOffset": 3 * round(compile_offset_seconds, 5),
                            "runOffset": round(run_offset_seconds, 5),
                            "memOffset": memory_offset_bytes,
                            "last_tune": DATE_TIME_INFO.get_datetime_now_formatted(
                                "%d.%m.%Y %H:%M:%S"
                            ),
                        }
                    },
                )
            except BaseException as exc:  # pylint:disable=W0718
                await send_alert(
                    "Tuner failure", f"language {language.short_name}\n{str(exc)}"
                )
                continue


if __name__ == "__main__":
    tuner = Tuner()
    asyncio.run(tuner.start())

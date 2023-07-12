"""Contains Custom Process class"""

from time import sleep
import subprocess
import concurrent.futures as pool
from typing import List, Callable, Any
import psutil
from custom_exceptions import (
    MemoryLimitException,
    RuntimeErrorException,
    TimeLimitException,
)
from settings import SETTINGS_MANAGER
from utils.basic import kill_process_tree


DEFAULT_MEM_LIMIT_BYTES = int(SETTINGS_MANAGER.limits.memory_mb) << 20  # MB to bytes
DEFAULT_TIME_LIMIT_SECONDS = SETTINGS_MANAGER.limits.time_seconds


class CustomProcess:
    """Custom Process class"""

    def __init__(self, cmd: List[str], get_memory_usage: Callable[[Any], float]):
        self.cmd = cmd
        self.get_memory_usage = get_memory_usage

        self.sleep_time = 0.05

    def _check_info(
        self, process: psutil.Popen, time_limit: float, memory_limit: float
    ):
        total_sleep = 0
        try:
            while process.is_running():
                cpu_time_usage = sum(process.cpu_times()[:-1])

                if cpu_time_usage > time_limit:
                    process.kill()
                    raise TimeLimitException("Time Limit")
                mem_usage = self.get_memory_usage(process.memory_info())  # bytes
                if mem_usage > memory_limit:
                    process.kill()
                    raise MemoryLimitException("Memory Limit")
                sleep(self.sleep_time)
                total_sleep += self.sleep_time
        except psutil.Error:  # pylint:disable=W0718
            return

    def run(
        self,
        input_data: str = "",
        time_limit: float = DEFAULT_TIME_LIMIT_SECONDS,
        memory_limit: float = DEFAULT_MEM_LIMIT_BYTES,
        time_offset: float = 0,
        memory_offset: float = 0,
    ) -> str:
        """Runs process with given constraints

        Args:
            input_data (str, optional):  input data. Defaults to "".
            time_limit (float, optional): time limit in seconds. Defaults to 10.
            memory_limit (float, optional): time limit in bytes. Defaults to 2^15.
            time_offset (float, optional): time offset in seconds. Defaults to 0.
            memory_offset (float, optional): memory offset in bytes. Defaults to 0.

        Returns:
            str: output of the process
        """
        time_bound = time_limit + time_offset
        memory_bound = memory_limit + memory_offset

        process = psutil.Popen(
            self.cmd,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf8",
        )

        with pool.ThreadPoolExecutor() as executor:
            info_process = executor.submit(
                self._check_info, process, time_bound, memory_bound
            )
            program_process = executor.submit(process.communicate, input=input_data)

        _ = info_process.result()
        result, _ = program_process.result()
        if process.returncode and process.returncode != 0:
            kill_process_tree(process.pid)
            raise RuntimeErrorException("Runtime error")
        kill_process_tree(process.pid)
        return result

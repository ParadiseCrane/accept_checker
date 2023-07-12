"""Contains Python Language class"""

from os import path
from typing import Any


from program_languages.basic import ProgramLanguage


class PythonLanguage(ProgramLanguage):
    """Python language class"""

    def get_offset_codes(self):
        return "a = 0", "while True: \n\t a = 0"

    def get_compile_extension(self):
        return "py"

    def get_run_extension(self):
        return "py"

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            "python",
            "-m",
            "py_compile",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            "python",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
        ]


PYTHON_LANGUAGE = PythonLanguage()

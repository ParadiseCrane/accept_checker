"""Contains Pascal Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class PascalLanguage(ProgramLanguage):
    """Pascal language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "pabcnetc"

    def get_offset_codes(self):
        return (
            "var i:integer; Begin i:=0;End.",
            "var i:integer; Begin while (true)  do i:=0; End.",
        )

    def get_compile_extension(self):
        return "pas"

    def get_run_extension(self):
        return "exe"

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            "mono",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
        ]


PASCAL_LANGUAGE = PascalLanguage()

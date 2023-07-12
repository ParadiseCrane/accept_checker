"""Contains Go Language class"""

from os import path
from typing import Any


from program_languages.basic import ProgramLanguage


class GoLanguage(ProgramLanguage):
    """Go language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "go"

    def get_offset_codes(self):
        return (
            "package main\n func main() { var a = 1 \na = a+1}",
            "package main\n func main() { for{} }",
        )

    def get_compile_extension(self):
        return "go"

    def get_run_extension(self):
        return ""

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            "build",
            "-o",
            folder_path,
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            path.abspath(path.join(folder_path, f"{program_name}")),
        ]


GO_LANGUAGE = GoLanguage()

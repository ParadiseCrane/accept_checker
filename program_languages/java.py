"""Contains Java Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class JavaLanguage(ProgramLanguage):
    """Java language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "javac"

    def get_offset_codes(self):
        return (
            "class Main\n{ public static void main(String args[])\n{\nSystem.out.println(1); } }",
            "class Main\n{ public static void main(String args[])\n  {\n    while(true){}\n  }\n}",
        )

    def get_compile_extension(self):
        return "java"

    def get_run_extension(self):
        return "java"

    def get_memory_usage(self, memory_info: Any):
        # print(f"{memory_info.data=}\n{memory_info.rss=}")
        return memory_info.rss

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            "java",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
        ]


JAVA_LANGUAGE = JavaLanguage()

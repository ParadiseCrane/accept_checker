"""Contains C# Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class CSharpLanguage(ProgramLanguage):
    """C# language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "mcs"

    def get_offset_codes(self):
        return (
            "using System; public class TEST { static public void Main() { int a = 0; }}",
            "using System; public class TEST {static public void Main(){int a;while(true){a = 0;}}}",
        )

    def get_compile_extension(self):
        return "cs"

    def get_run_extension(self):
        return "exe"

    def get_memory_usage(self, memory_info: Any):
        # print(f"{memory_info.data=}\n{memory_info.rss=}\n")
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
            "mono",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
        ]


CSHARP_LANGUAGE = CSharpLanguage()

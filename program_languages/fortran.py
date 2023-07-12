"""Contains Rust Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class FortranLanguage(ProgramLanguage):
    """Fortran language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "gfortran"

    def get_offset_codes(self):
        time_offset_code = "program hello\n\tinteger :: a\n\ta = 10\nend program hello"

        memory_offset_code = (
            "program hello\n"
            "\tinteger :: a\n"
            "\tdo while (1 == 1)\n"
            "\t\ta = 10\n"
            "\tend do\n"
            "end program hello"
        )

        return (
            time_offset_code,
            memory_offset_code,
        )

    def get_compile_extension(self):
        return "f90"

    def get_run_extension(self):
        return ""

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
            "-o",
            path.abspath(path.join(folder_path, f"{program_name}")),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            path.abspath(path.join(folder_path, f"{program_name}")),
        ]


FORTRAN_LANGUAGE = FortranLanguage()

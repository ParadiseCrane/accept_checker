"""Contains Cobol Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class CobolLanguage(ProgramLanguage):
    """Cobol language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "cobc"

    def get_offset_codes(self):
        time_offset_code = (
            "\t\tIDENTIFICATION DIVISION.\n"
            "\t\tPROGRAM-ID. TEST.\n"
            "\t\tENVIRONMENT DIVISION.\n"
            "\t\tDATA DIVISION.\n"
            "\t\tWORKING-STORAGE SECTION.\n"
            "\t\t\t\t01 Variable PIC 9 VALUE 0.\n"
            "\t\tPROCEDURE DIVISION.\n"
            "\t\t\t\tSET Variable TO 1.\n"
            "\t\t\t\tSTOP RUN.\n"
            "\t\tEND PROGRAM TEST.\n"
        )
        mem_offset_code = (
            "\t\tIDENTIFICATION DIVISION.\n"
            "\t\tPROGRAM-ID. TEST.\n"
            "\t\tENVIRONMENT DIVISION.\n"
            "\t\tDATA DIVISION.\n"
            "\t\tWORKING-STORAGE SECTION.\n"
            "\t\t\t\t01 Variable PIC 9 VALUE 0.\n"
            "\t\tPROCEDURE DIVISION.\n"
            "\t\tPERFORM UNTIL 1 < 0\n"
            "\t\t\t\tSET Variable TO 0\n"
            "\t\tEND-PERFORM\n"
            "\t\tSTOP RUN.\n"
            "\t\tEND PROGRAM TEST.\n"
        )
        return (
            time_offset_code,
            mem_offset_code,
        )

    def get_compile_extension(self):
        return "cob"

    def get_run_extension(self):
        return ""

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            "-x",
            "-o",
            path.abspath(path.join(folder_path, program_name)),
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [path.abspath(path.join(folder_path, f"{program_name}"))]


COBOL_LANGUAGE = CobolLanguage()

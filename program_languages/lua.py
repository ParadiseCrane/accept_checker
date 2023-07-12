"""Contains Lua Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class LuaLanguage(ProgramLanguage):
    """Lua language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "luac"

    def get_offset_codes(self):
        return (
            "a=1",
            "while true do\nend",
        )

    def get_compile_extension(self):
        return "lua"

    def get_run_extension(self):
        return "out"

    def get_memory_usage(self, memory_info: Any):
        return memory_info.data

    def get_cmd_compile(self, folder_path: str, program_name: str):
        return [
            self.compiler_path,
            "-o",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_compile_extension()}")
            ),
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [
            "lua",
            path.abspath(
                path.join(folder_path, f"{program_name}.{self.get_run_extension()}")
            ),
        ]


LUA_LANGUAGE = LuaLanguage()

"""Contains Cpp Language class"""

from os import path
from typing import Any

from program_languages.basic import ProgramLanguage


class HaskellLanguage(ProgramLanguage):
    """Haskell language class"""

    def __init__(self):
        super().__init__()
        self.compiler_path: str = "ghc"

    def get_offset_codes(self):
        return (
            'main :: IO ()\nmain = putStrLn "Hello, World!"',
            "infi=infi\nmain = infi",
        )

    def get_compile_extension(self):
        return "hs"

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
        ]

    def get_cmd_run(self, folder_path: str, program_name: str):
        return [path.abspath(path.join(folder_path, f"{program_name}"))]


HASKELL_LANGUAGE = HaskellLanguage()

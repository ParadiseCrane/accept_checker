"""Contains Basic Language class"""

from typing import List, Tuple, Any


class ProgramLanguage:
    """Basic language abstract class"""

    def get_offset_codes(self) -> Tuple[str, str]:
        """Returns offset information for the language

        Returns:
            tuple[str, str]: (time offset code, memory offset code)
        """

        raise NotImplementedError

    def get_compile_extension(self) -> str:
        """Returns compile extension for the language

        Returns:
            str: extension without leading dot
        """

        raise NotImplementedError

    def get_run_extension(self) -> str:
        """Returns run extension for the language

        Returns:
            str: extension without leading dot
        """

        raise NotImplementedError

    def get_memory_usage(self, memory_info: Any) -> float:
        """Returns memory usage of the program in bytes

        Args:
            memory_info: psutil.Popen process memory info


        Returns:
            float: memory usage of programs in bytes
        """

        raise NotImplementedError

    def get_cmd_compile(self, folder_path: str, program_name: str) -> List[str]:
        """Returns cmd command to compile the program

        Args:
            folder_path: path to the testing folder
            program_name: name of the testing program

        Returns:
            list[str]: cmd command to compile the program
        """

        raise NotImplementedError

    def get_cmd_run(self, folder_path: str, program_name: str) -> List[str]:
        """Returns cmd command to run the program

        Args:
            folder_path: path to the testing folder
            program_name: name of the testing program

        Returns:
            list[str]: cmd command to run the program
        """

        raise NotImplementedError

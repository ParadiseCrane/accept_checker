"""Contain custom exceptions"""


class CompilationErrorException(Exception):
    """Checker compilation error"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class TimeLimitException(Exception):
    """Process Time Limit exception"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MemoryLimitException(Exception):
    """Process Memory Limit exception"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class RuntimeErrorException(Exception):
    """Process Runtime Error exception"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ServerErrorException(Exception):
    """Process Runtime Error exception"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

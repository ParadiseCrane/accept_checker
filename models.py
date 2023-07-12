"""Contains data models"""
from typing import List, Any, Dict


class PendingQueueItem:
    """Pending queue item model"""

    class Checker:
        """PendingQueueItem Checker class"""

        def __init__(self, checker_dict: Dict[str, Any]) -> None:
            self.language: int = checker_dict["language"]
            self.source_code: str = checker_dict["sourceCode"]

        def to_dict(self) -> Dict[str, Any]:
            """Converts class to dict object

            Returns:
                dict
            """
            return {
                "language": self.language,
                "sourceCode": self.source_code,
            }

    def __init__(self, item_dict: Dict[str, Any]) -> None:
        self.task_type: int = item_dict["taskType"]
        self.task_check_type: int = item_dict["taskCheckType"]
        self.checker = None
        if item_dict["checker"] is not None:
            self.checker = self.Checker(item_dict["checker"])

    def to_dict(self) -> Dict[str, Any]:
        """Converts class to dict object

        Returns:
            dict
        """
        return {
            "taskType": self.task_type,
            "taskCheckType": self.task_check_type,
            "checker": self.checker.to_dict() if self.checker else None,
        }


class Attempt:
    """Attempt model"""

    class Constraints:
        """Constraints model"""

        def __init__(self, constraints_dict: Dict[str, Any]):
            self.time = constraints_dict["time"]
            self.memory = constraints_dict["memory"]

        def to_dict(self) -> Dict[str, Any]:
            """Converts class to dict object

            Returns:
                dict
            """
            return {
                "time": self.time,
                "memory": self.memory,
            }

    class Result:
        """Attempt result model"""

        class Test:
            """Result test model"""

            def __init__(self, test_dict: Dict[str, Any]) -> None:
                self.input_data: str = test_dict["inputData"]
                self.output_data: str = test_dict["outputData"]

            def to_dict(self):
                """Converts class to dict object

                Returns:
                    dict
                """
                return {"inputData": self.input_data, "outputData": self.output_data}

        def __init__(self, result_dict: Dict[str, Any]):
            self.test = self.Test(result_dict["test"])
            self.verdict: int = result_dict["verdict"]

        def to_dict(self):
            """Converts class to dict object

            Returns:
                dict
            """
            return {
                "test": self.test.to_dict(),
                "verdict": self.verdict,
            }

    def __init__(self, attempt_dict: Dict[str, Any]):
        self.spec: str = attempt_dict["spec"]
        self.language: str = attempt_dict["language"]
        self.status: int = attempt_dict["status"]
        self.constraints = self.Constraints(attempt_dict["constraints"])
        self.program_text: str = attempt_dict["programText"]
        self.text_answers: List[str] = attempt_dict["textAnswers"]
        self.date: str = attempt_dict["date"]
        self.results = [self.Result(result) for result in attempt_dict["results"]]
        self.verdict: int = attempt_dict["verdict"]
        self.logs: List[str] = attempt_dict["logs"]

    def to_dict(self):
        """Converts class to dict object

        Returns:
            dict
        """
        return {
            "spec": self.spec,
            "language": self.language,
            "status": self.status,
            "constraints": self.constraints.to_dict(),
            "program_text": self.program_text,
            "textAnswers": self.text_answers,
            "date": self.date,
            "results": self.results,
            "verdict": self.verdict,
            "logs": self.logs,
        }


class Language:
    """Language model"""

    def __init__(self, language_dict: Dict[str, Any]):
        self.spec: int = int(language_dict["spec"])

        self.short_name: str = language_dict["shortName"]
        self.run_offset: float = language_dict["runOffset"]
        self.compile_offset: float = language_dict["compileOffset"]
        self.mem_offset: float = language_dict["memOffset"]

    def to_dict(self):
        """Converts class to dict object

        Returns:
            dict
        """
        return {
            "spec": self.spec,
            "shortName": self.short_name,
            "runOffset": self.run_offset,
            "compileOffset": self.compile_offset,
            "memOffset": self.mem_offset,
        }

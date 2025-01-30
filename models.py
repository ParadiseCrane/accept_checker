"""Contains data models"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskTest:
    spec: str
    input_data: str
    output_data: str


@dataclass
class Language:
    spec: int
    name: str
    shortName: str
    extensions: list[str]
    runOffset: float
    compileOffset: float
    memOffset: int


@dataclass
class Checker:
    language: Language
    sourceCode: str


@dataclass
class Constraints:
    time: float
    memory: int


@dataclass
class Task:
    spec: str
    tests: list[TaskTest]
    test_groups: list[int]
    checkType: int
    taskType: int
    constraints: Constraints
    checker: Optional[Checker]


@dataclass
class Attempt:
    spec: str
    programText: str
    textAnswers: list[str]
    language: Language
    date: str
    organization: str
    task: Task
    author: str


@dataclass
class Result:
    test: str
    verdict: int


@dataclass
class ProcessedAttempt:
    spec: str
    programText: str
    language: int
    date: str
    organization: str
    author: str
    results: list[Result]
    verdict: int
    verdictTest: int
    logs: list[str]

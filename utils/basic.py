"""General utilities functions"""

import os
import shutil
import sys
import time
from datetime import datetime, timezone
from typing import Literal

import psutil

from database import Database
from models import Attempt
from settings import SETTINGS_MANAGER
from utils.soft_mkdir import soft_mkdir

VerdictType = Literal[
    "OK",
    "TL",
    "WA",
    "CE",
    "RE",
    "SE",
    "NT",
    "ML",
    "CH",
]

VERDICT_DICT: dict[VerdictType, int] = dict(
    {
        "OK": 0,
        "TL": 1,
        "WA": 2,
        "CE": 3,
        "RE": 4,
        "SE": 5,
        "NT": 6,
        "ML": 7,
        "CH": 8,
    }
)


ATTEMPT_STATUS_DICT = dict(
    {
        "pending": 0,
        "testing": 1,
        "finished": 2,
        "banned": 3,
    }
)

AttemptStatusType = Literal[
    "pending",
    "testing",
    "finished",
    "banned",
]

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)


def map_verdict(
    verdict: VerdictType,
) -> int:
    """Maps string verdict to its spec

    Args:
        verdict (VERDICT_TYPE): string verdict

    Returns:
        int: verdict spec
    """
    return VERDICT_DICT[verdict]


def generate_tests_verdicts(
    verdict: VerdictType,
    tests_number: int,
) -> list[int]:
    """Generates same verdict for all tests

    Args:
        verdict (VERDICT_TYPE): string verdict
        tests_number (int): number of tests

    Returns:
        list[int]: verdict specs
    """
    verdict_spec = VERDICT_DICT[verdict]
    return [verdict_spec for _ in range(tests_number)]


def map_attempt_status(
    attempt_status: AttemptStatusType,
) -> int:
    """Maps attempt status verdict to its spec

    Args:
        attempt_status (ATTEMPT_STATUS_TYPE): string attempt status

    Returns:
        int: attempt status spec
    """
    return ATTEMPT_STATUS_DICT[attempt_status]


async def send_alert(
    title: str,
    message: str,
    status: str = "error",
):
    """Saves alert to the database

    Args:
        title (str): alert title
        message (str): message
        status (str, optional): Status code. Defaults to "error".
    """

    alert = dict(
        {
            "title": title,
            "date": datetime.now(timezone.utc),
            "message": message,
            "status": status,
        }
    )

    await Database().insert_one("checker_alert", alert)


def delete_folder(path: str):
    """Deletes specified folder

    Args:
        path (str): path to the folder
    """
    if os.path.exists(path) and os.path.isdir(path):
        try:
            shutil.rmtree(
                path,
                ignore_errors=True,
            )
        except BaseException:  # pylint: disable=W0718
            time.sleep(1)
            shutil.rmtree(
                path,
                ignore_errors=True,
            )


def create_program_folder(
    attempt_spec: str,
) -> str:
    """Creates folder based on attempt spec

    Args:
        attempt_spec (str): attempt spec

    Returns:
        str: path to the folder
    """
    folder_name = f"{attempt_spec}_{int(datetime.utcnow().timestamp()*10**6)}"
    folder_path = os.path.abspath(
        os.path.join(
            SETTINGS_MANAGER.manager.attempts_folder_path,
            folder_name,
        )
    )
    soft_mkdir(folder_path)
    return folder_path


def kill_process_tree(
    pid: int,
):
    """Kills process tree

    Args:
        pid (int): pid of the process
    """
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except BaseException:  # pylint:disable=W0718
        pass


def generate_program_name(
    attempt: Attempt,
) -> str:
    """Generates program name based on attempt

    Args:
        attempt (Attempt): attempt object

    Returns:
        str: program name
    """
    return attempt.spec[:16]


def group_values(
    values: list,
    group_division: list[int],
) -> list:
    """Groups values based on slice indexes

    Args:
        values (list): data to group
        group_division (list[int]): grouping index slices

    Returns:
        list: grouped values
    """

    grouped_values = []

    values_len = len(values)
    for i in range(1, len(group_division)):
        start_idx_inc = group_division[i - 1] + 1
        end_idx_exc = group_division[i]

        if start_idx_inc > values_len:
            break

        grouped_values.append(values[start_idx_inc : end_idx_exc + 1])

    return grouped_values


def prepare_test_groups(
    test_groups: list[int],
    total_tests: int,
) -> list[int]:
    """Prepares test_groups from database for
    further using in group_values function

    Args:
        test_groups (list[int]): grouping index slices
        total_tests (int): total number of tests in the task

    Returns:
        list[int]: prepared test_groups
    """
    return [-1] + test_groups + [total_tests - 1]

"""Contains the SettingsManager class instances"""
import os
import json

from utils.soft_mkdir import soft_mkdir
from typing import Any, Dict


class ManagerSettings:
    """Checker manager class"""

    def __init__(
        self,
        attempts_folder: str,
    ) -> None:
        self.attempts_folder = attempts_folder
        path = os.path.join(".", attempts_folder)
        soft_mkdir(path)
        self.attempts_folder_path = path

    def as_dict(self) -> Dict[str, Any]:
        """Represents the class instance as dict

        Returns:
            dict
        """
        return {"attempts_folder": self.attempts_folder}


class ListenerSettings:
    """Checker listener class"""

    def __init__(
        self,
        sleep_timeout_seconds: float,
        langs_refetch_timeout_minutes: float,
        cpu_utilization_fraction: float,
    ) -> None:
        self.sleep_timeout_seconds = sleep_timeout_seconds
        self.langs_refetch_timeout_minutes = langs_refetch_timeout_minutes
        self.cpu_utilization_fraction = cpu_utilization_fraction

    def as_dict(self) -> Dict[str, Any]:
        """Represents the class instance as dict

        Returns:
            dict
        """
        return {
            "sleep_timeout_seconds": self.sleep_timeout_seconds,
            "langs_refetch_timeout_minutes": self.langs_refetch_timeout_minutes,
            "cpu_utilization_fraction": self.cpu_utilization_fraction,
        }


class SchedulerSettings:
    """Scheduler settings class"""

    def __init__(self, scheduler_dict: Dict[str, Any]) -> None:
        self.day_of_week: int = scheduler_dict["day_of_week"]
        self.hour: int = scheduler_dict["hour"]
        self.minute: int = scheduler_dict["minute"]

    def as_dict(self) -> Dict[str, Any]:
        """Represents the class instance as dict

        Returns:
            dict
        """
        return {
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "minute": self.minute,
        }


class TunerSettings:
    """Tuner settings class"""

    def __init__(self, tuner_dict: Dict[str, Any]) -> None:
        self.scheduler = SchedulerSettings(tuner_dict["scheduler"])
        self.tests_folder: str = tuner_dict["tests_folder"]
        self.test_runs_count: int = int(tuner_dict["test_runs_count"])

    def as_dict(self) -> Dict[str, Any]:
        """Represents the class instance as dict

        Returns:
            dict
        """
        return {
            "scheduler": self.scheduler.as_dict(),
            "tests_folder": self.tests_folder,
            "test_runs_count": self.test_runs_count,
        }


class DefaultLimits:
    """Default checker limits class class"""

    def __init__(
        self,
        time_seconds: float,
        memory_mb: float,
    ) -> None:
        self.time_seconds = time_seconds
        self.memory_mb = memory_mb

    def as_dict(self) -> Dict[str, Any]:
        """Represents the class instance as dict

        Returns:
            dict
        """
        return {
            "time_seconds": self.time_seconds,
            "memory_mb": self.memory_mb,
        }


class SettingsManager:
    """Checker settings manager"""

    def _pack_manager(self):
        self.manager = ManagerSettings(
            attempts_folder=self._settings["manager"]["attempts_folder"]
        )

    def _pack_listener(self):
        self.listener = ListenerSettings(
            sleep_timeout_seconds=self._settings["listener"]["sleep_timeout_seconds"],
            langs_refetch_timeout_minutes=self._settings["listener"][
                "langs_refetch_timeout_minutes"
            ],
            cpu_utilization_fraction=self._settings["listener"][
                "cpu_utilization_fraction"
            ],
        )

    def _pack_tuner(self):
        self.tuner = TunerSettings(self._settings["tuner"])

    def _pack_limits(self):
        self.limits = DefaultLimits(
            time_seconds=self._settings["default_limits"]["time_seconds"],
            memory_mb=self._settings["default_limits"]["memory_mb"],
        )

    def _load_settings(self):
        with open(self._path, encoding="utf8") as json_file:
            self._settings: Dict[str, Any] = json.load(json_file)
            json_file.close()

    def __str__(self) -> str:
        return str(list(self._settings.items()))

    def __repr__(self) -> str:
        return str(list(self._settings.items()))

    def __init__(self, path: str = os.path.join(".", "settings.json")) -> None:
        self._path = path
        self._load_settings()

        self._pack_listener()
        self._pack_manager()
        self._pack_tuner()
        self._pack_limits()


SETTINGS_MANAGER = SettingsManager()

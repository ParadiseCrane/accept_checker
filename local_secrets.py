"""Contains the SecretsManager class instances"""

import os
from typing import Any, Dict

import dotenv


class SecretsManager:
    """Manages secrets from .env file"""

    def __init__(self, path: str = os.path.join(".", ".env")) -> None:
        self._path = path
        self._secrets: Dict[str, Any] = dotenv.dotenv_values(self._path)
        self._mongodb_connection_string: str = self._secrets["CONNECTION_STRING"]  # type: ignore
        self._mongodb_database_name: str = self._secrets["DATABASE_NAME"]  # type: ignore

    def get_connection_string(self) -> str:
        """Returns MongoDB connection string

        Returns:
            str: MongoDB connection string
        """
        return self._mongodb_connection_string

    def get_database_name(self) -> str:
        """Returns MongoDB database name

        Returns:
            str: MongoDB database name
        """
        return self._mongodb_database_name


SECRETS_MANAGER = SecretsManager()

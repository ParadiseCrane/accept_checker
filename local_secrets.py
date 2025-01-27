"""Contains the SecretsManager class instances"""

import os
from typing import Any

import dotenv


class SecretsManager:
    """Manages secrets from .env file"""

    def __init__(self, path: str = os.path.join(".", ".env")) -> None:
        self._path = path
        self._secrets: dict[str, Any] = dotenv.dotenv_values(self._path)
        self._mongodb_connection_string: str = self._secrets["CONNECTION_STRING"]
        self._mongodb_database: str = self._secrets["DATABASE"]
        self._kafka_connection_string: str = self._secrets["KAFKA_CONNECTION"]
        self._debug = bool(self._secrets["DEBUG"])

    @property
    def debug(self) -> bool:
        """Returns debug flag

        Returns:
            bool: debug flag
        """
        return self._debug

    @property
    def connection_string(self) -> str:
        """Returns MongoDB connection string

        Returns:
            str: MongoDB connection string
        """
        return self._mongodb_connection_string

    @property
    def database(self) -> str:
        """Returns MongoDB database name

        Returns:
            str: MongoDB database name
        """
        return self.database

    @property
    def kafka_string(self) -> str:
        """Returns Kafka port to listen

        Returns:
            str: Kafka connection string
        """
        return self._kafka_connection_string


SECRETS_MANAGER = SecretsManager()

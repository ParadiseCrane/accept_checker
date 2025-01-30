"""Contains the SecretsManager class instances"""

import os

from dotenv import load_dotenv

load_dotenv()


class SecretsManager:
    """Manages secrets from .env file"""

    def __init__(self, path: str = os.path.join(".", ".env")) -> None:
        self._path = path
        self._mongodb_connection_string: str = os.getenv("CONNECTION_STRING") or ""
        self._mongodb_database: str = os.getenv("DATABASE") or "test"
        self._kafka_connection_string: str = (
            os.getenv("KAFKA_CONNECTION") or "localhost:9092"
        )
        self._debug = bool(os.getenv("DEBUG"))

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
        return self._mongodb_database

    @property
    def kafka_string(self) -> str:
        """Returns Kafka port to listen

        Returns:
            str: Kafka connection string
        """
        return self._kafka_connection_string


SECRETS_MANAGER = SecretsManager()

"""Contains the SecretsManager class instances"""

import os
import dotenv
from typing import Any, Dict


class SecretsManager:
    """Manages secrets from .env file"""

    def __init__(self, path: str = os.path.join(".", ".env")) -> None:
        self._path = path
        self._secrets: Dict[str, Any] = dotenv.dotenv_values(self._path)
        self._mongodb_connection_string: str = self._secrets["CONNECTION_STRING"]  # type: ignore

    def get_connection_string(self) -> str:
        """Returns MongoDB connection string

        Returns:
            str: MongoDB connection string
        """
        return self._mongodb_connection_string


SECRETS_MANAGER = SecretsManager()

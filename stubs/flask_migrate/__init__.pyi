from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


class Migrate:
    def __init__(self, app: Flask | None = ..., db: SQLAlchemy | None = ..., directory: str = ..., **kwargs: Any) -> None: ...

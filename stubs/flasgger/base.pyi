from typing import Any, Optional, List, Callable

from flask import Flask


class Swagger:
    def init_app(self, app: Flask, decorators: Any | None = ...) -> None: ...
    def definition(self, name: str, tags: Optional[List[str]] = ...) -> Callable: ...

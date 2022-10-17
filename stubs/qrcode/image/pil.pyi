from typing import Any, BinaryIO


class PilImage:
    def save(self, stream: BinaryIO, format: str=None, **kwargs: Any) -> None: ...
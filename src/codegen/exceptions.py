"""
This module contains the exceptions for the code generation.
"""

from typing import Union


class GenerationError(Exception):
    def __init__(self, caption: str, message: Union[str, list[str]]):
        self.caption = caption
        self.message = "\n".join(message) if isinstance(message, list) else message
        super().__init__(self.caption, self.message)

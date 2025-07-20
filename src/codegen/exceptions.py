"""
This module contains the exceptions for the code generation.
"""


class GenerationError(Exception):
    def __init__(self, caption, message: str | list[str]):
        self.caption = caption
        self.message = "\n".join(message) if isinstance(message, list) else message
        super().__init__(self.caption, self.message)

from typing import Protocol, Union

from tcutility import results


class WordFormatter(Protocol):
    """Base protocol for formatters that write content to a Word document. Every class with the `write` method should inherit from this protocol."""

    def write(self, *results: Union[results.Result, str]) -> str: ...

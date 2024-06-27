from typing import Protocol, Sequence

from tcutility import results


class WordFormatter(Protocol):
    """Base protocol for formatters that write content to a Word document. Every class with the `write` method should inherit from this protocol."""

    def write(self, results: results.Result | Sequence[results.Result]) -> str: ...

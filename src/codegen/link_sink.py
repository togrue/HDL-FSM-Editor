"""Protocol for recording HDL-to-source links during generation. GUI passes LinkDictionary; script mode passes None."""

from typing import Any, Protocol


class LinkSink(Protocol):
    """Protocol for recording links from generated HDL lines to UI source (tabs/widgets)."""

    def add(
        self,
        file_name: str,
        file_line_number: int,
        hdl_item_type: str,
        number_of_lines: int,
        hdl_item_name: str | Any,
    ) -> None:
        """Register a link from (file_name, line) to the given tab/widget for HDL navigation."""
        ...

    def clear_link_dict(self, file_name: str) -> None:
        """Remove all link entries for the given file name."""
        ...

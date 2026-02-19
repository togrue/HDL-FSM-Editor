"""
Design data for HDL generation. No element or canvas imports.
Populated by design_data_gatherer; read by codegen.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DesignData:
    """Gathered design data (strings + widget refs for link_dict)."""

    # reset condition and action: (condition_text, action_text_from_widget, condition_ref, action_ref).
    # action_text_from_widget is the user text only; codegen prepends "state <= X;\n".
    # None, when no reset condition is specified (codegen raises).
    reset_condition_action: tuple[str, str, Any, Any] | None

    global_actions_before: tuple[str, Any] = ("", None)
    global_actions_after: tuple[str, Any] = ("", None)
    concurrent_actions: tuple[str, Any] = ("", None)
    state_comments_by_state_tag: dict[str, tuple[str | None, Any | None]] | None = None
    state_tag_list_sorted: list[str] | None = None
    condition_action_by_canvas_id: dict[int, tuple[str, str, Any, Any]] | None = None
    state_actions_default: tuple[str, Any] = ("", None)
    state_action_list: list[tuple[str, str, Any]] | None = None

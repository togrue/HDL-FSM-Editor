"""
Design data for HDL generation. No element or canvas imports.
Populated by design_data_gatherer; read by codegen.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DesignData:
    """Gathered design data (strings + widget refs for link_dict)."""

    # Control-tab / config (module name, language, reset/clock signal names).
    language: str = "VHDL"
    module_name: str = ""
    reset_signal_name: str = ""
    clock_signal_name: str = ""

    # Reset transition: condition and action for the single reset transition.
    # Tuple: (condition_text, action_text_from_widget, condition_ref, action_ref).
    # action_text_from_widget is user text only; codegen prepends "state <= X;\n".
    # None when no reset condition is specified (codegen raises).
    reset_condition_action: tuple[str, str, Any, Any] | None = None
    # Reset target state name (display name of state reached by active reset). None when no reset transition.
    reset_target_state_name: str | None = None

    # Interface text widgets: (content, widget_ref for link_dict).
    # Content normalized like get_text_from_text_widget (single newline -> empty string).
    interface_package_text: tuple[str, Any] = ("", None)
    interface_generics_text: tuple[str, Any] = ("", None)
    interface_ports_text: tuple[str, Any] = ("", None)

    # Internals text widgets: (content, widget_ref for link_dict). Same convention as interface.
    internals_package_text: tuple[str, Any] = ("", None)
    internals_architecture_text: tuple[str, Any] = ("", None)
    internals_process_clocked_text: tuple[str, Any] = ("", None)
    internals_process_combinatorial_text: tuple[str, Any] = ("", None)

    # Global actions emitted before the main state/transition logic (e.g. declarations).
    # Tuple: (full_text_incl_comment_line, widget_ref for link_dict).
    global_actions_before: tuple[str, Any] = ("", None)
    # Global actions emitted after the main state/transition logic.
    # Tuple: (full_text_incl_comment_line, widget_ref for link_dict).
    global_actions_after: tuple[str, Any] = ("", None)
    # Concurrent (combinational) actions block; generated outside the clocked process.
    # Tuple: (full_text_incl_comment_line, widget_ref for link_dict).
    concurrent_actions: tuple[str, Any] = ("", None)

    # Per-state comment lines for documentation in generated HDL.
    # Key: state_tag. Value: (comment_text_or_None, widget_ref_or_None).
    state_comments_by_state_tag: dict[str, tuple[str | None, Any | None]] | None = None
    # Ordered list of state tags (e.g. for deterministic emission order).
    state_tag_list_sorted: list[str] | None = None
    # Display name for each state tag (canvas label text for case/state names in HDL).
    state_name_by_state_tag: dict[str, str] | None = None

    # Per-transition condition and action: keyed by canvas arc id.
    # Value: (condition_text, action_text, condition_ref, action_ref) for link_dict.
    condition_action_by_canvas_id: dict[int, tuple[str, str, Any, Any]] | None = None

    # Per-transition target and condition/action: keyed by transition_tag (e.g. "transition5").
    # Value: (target, condition_text, action_text, condition_ref, action_ref).
    # target is state display name or "connector<n>"; refs are None when no condition/action box.
    transition_data_by_transition_tag: dict[str, tuple[str, str, str, Any | None, Any | None]] | None = None

    # Default (else/others) branch actions in the main state machine.
    # Tuple: (full_text_incl_comment_line, widget_ref for link_dict).
    state_actions_default: tuple[str, Any] = ("", None)
    # Per-state action blocks (e.g. output assignments when in that state).
    # List of (state_name, action_text, widget_ref); order matches state_tag_list_sorted.
    state_action_list: list[tuple[str, str, Any]] | None = None

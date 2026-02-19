"""
Gathers design data from elements and canvas for HDL generation.
Imports elements; callers pass DesignData into codegen.
"""

from design_data import DesignData
from project_manager import project_manager


def _get_reset_transition_tag() -> str:
    reset_entry_tags = project_manager.canvas.gettags("reset_entry")
    for t in reset_entry_tags:
        if t.startswith("transition"):  # look for transition<n>_start
            return t[:-6]
    return ""


def gather_design_data() -> DesignData:
    """Build DesignData from canvas and element ref_dicts. Call before run_hdl_generation."""
    from elements import condition_action

    reset_condition_action: tuple[str, str, object, object] | None = None
    reset_transition_tag = _get_reset_transition_tag()
    if reset_transition_tag:
        tags = project_manager.canvas.gettags(reset_transition_tag)
        for tag in tags:
            if tag.startswith("ca_connection"):  # ca_connection<n>_end
                condition_action_number = tag[13:-4]
                condition_action_tag = "condition_action" + condition_action_number
                canvas_ids = project_manager.canvas.find_withtag(condition_action_tag)
                if canvas_ids:
                    ref = condition_action.ConditionAction.ref_dict.get(canvas_ids[0])
                    if ref is not None:
                        condition_text = ref.condition_id.get("1.0", "end-1c")
                        action_text = ref.action_id.get("1.0", "end")
                        reset_condition_action = (
                            condition_text,
                            action_text,
                            ref.condition_id,
                            ref.action_id,
                        )
                break

    return DesignData(
        reset_condition_action=reset_condition_action,
    )

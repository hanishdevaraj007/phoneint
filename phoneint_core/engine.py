"""
phoneint_core.engine

The backbone of PhoneINT. Takes a raw number string, validates/parses it,
runs every registered plugin (respecting dependencies), and returns a
single InvestigationReport. The CLI, GUI, and batch mode all call this
same function — no duplicated logic anywhere else.
"""

import phonenumbers

from phoneint_core.models import InvestigationReport, PluginResult
from phoneint_core.plugins import PLUGIN_REGISTRY


class NumberParseError(Exception):
    """Raised when the input string can't be parsed into a valid number."""


def parse_and_validate(raw_number: str) -> phonenumbers.PhoneNumber:
    """
    Parses and validates a raw phone number string.
    Raises NumberParseError with a human-readable message on failure —
    callers (CLI/GUI) decide how to display that, the engine doesn't print.
    """
    try:
        parsed = phonenumbers.parse(raw_number, None)
    except phonenumbers.phonenumberutil.NumberParseException as e:
        raise NumberParseError(f"Parse error: {e}") from e

    if not phonenumbers.is_valid_number(parsed):
        raise NumberParseError("Invalid phone number.")

    return parsed


def _order_plugins(plugins):
    """
    Simple dependency ordering: plugins with no dependencies first,
    then plugins whose dependencies have already been placed.
    Sufficient for the shallow (one-level) dependency graphs this
    project uses; can be swapped for a real topological sort later
    if plugins start depending on each other more deeply.
    """
    ordered = []
    remaining = list(plugins)

    while remaining:
        progressed = False
        placed_names = {p.name for p in ordered}

        for plugin in list(remaining):
            if all(dep in placed_names for dep in plugin.depends_on):
                ordered.append(plugin)
                remaining.remove(plugin)
                progressed = True

        if not progressed:
            # Circular or unresolvable dependency — append the rest as-is
            # rather than looping forever. Their `context` will just be
            # missing some entries and they should handle that gracefully.
            ordered.extend(remaining)
            break

    return ordered


def run_investigation(raw_number: str, plugins=None) -> InvestigationReport:
    """
    The main entry point. Everything else in the project (CLI, GUI,
    batch mode) should call this instead of touching plugins directly.
    """
    parsed = parse_and_validate(raw_number)
    report = InvestigationReport(target=raw_number)

    active_plugins = plugins if plugins is not None else PLUGIN_REGISTRY
    ordered_plugins = _order_plugins(active_plugins)

    for plugin in ordered_plugins:
        context = {dep: report.get(dep) for dep in plugin.depends_on}
        result: PluginResult = plugin.safe_run(parsed, context)
        report.add_result(result)

    return report

"""
phoneint_core.models

Structured data objects passed between the engine and plugins.
Using dataclasses instead of loose dicts keeps plugin output predictable
and makes it easy to add correlation/scoring logic later without
re-parsing free-form dictionaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class PluginResult:
    """
    The standard return type every plugin must produce.

    plugin_name : str
        Identifier of the plugin that produced this result (e.g. "validation").
    status : str
        One of "ok", "error", "skipped".
    data : dict
        The plugin's actual findings, e.g. {"Carrier": "Airtel", ...}.
    error : Optional[str]
        Populated when status == "error".
    """
    plugin_name: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class InvestigationReport:
    """
    The full output of a run: one target number, many plugin results.
    This is what the CLI/GUI/report-exporters all consume.
    """
    target: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    results: dict[str, PluginResult] = field(default_factory=dict)

    def add_result(self, result: PluginResult) -> None:
        self.results[result.plugin_name] = result

    def get(self, plugin_name: str) -> Optional[PluginResult]:
        return self.results.get(plugin_name)

    def to_dict(self) -> dict:
        """Flatten into a plain dict — used by JSON export and the GUI."""
        return {
            "target": self.target,
            "timestamp": self.timestamp,
            "results": {
                name: {
                    "status": r.status,
                    "data": r.data,
                    "error": r.error,
                }
                for name, r in self.results.items()
            },
        }
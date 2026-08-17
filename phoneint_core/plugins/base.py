"""
phoneint_core.plugins.base

Every plugin (existing or contributed) implements this interface.
The engine discovers plugins by finding subclasses of PluginBase and
calls .run(parsed_number) on each one.

To add a new intelligence source:
    1. Create a new file in phoneint_core/plugins/
    2. Subclass PluginBase
    3. Set `name` and implement `run()`
    4. Register it in phoneint_core/plugins/__init__.py's PLUGIN_REGISTRY

No engine code needs to change to add a plugin.
"""

from abc import ABC, abstractmethod
from phoneint_core.models import PluginResult


class PluginBase(ABC):
    # Unique short identifier, used as the key in InvestigationReport.results
    name: str = "base"

    # Whether this plugin needs network access. The engine can use this
    # later to support an --offline mode.
    requires_network: bool = False

    # Names of other plugins whose results this plugin needs to see.
    # The engine guarantees those plugins run first and passes their
    # results in via `context`. Leave empty for independent plugins.
    depends_on: list[str] = []

    @abstractmethod
    def run(self, parsed_number, context: dict[str, PluginResult] | None = None) -> PluginResult:
        """
        parsed_number: a phonenumbers.PhoneNumber object (already parsed
                        and validated by the engine before plugins run).
        context: results from plugins listed in `depends_on`, keyed by
                 plugin name. Empty dict for independent plugins.

        Must return a PluginResult. Must NOT raise — catch your own
        exceptions and return status="error" with the message in `error`.
        """
        raise NotImplementedError

    def safe_run(self, parsed_number, context: dict[str, PluginResult] | None = None) -> PluginResult:
        """
        Wrapper the engine actually calls. Guarantees a plugin crash
        can't take down the whole investigation.
        """
        try:
            return self.run(parsed_number, context or {})
        except Exception as e:
            return PluginResult(plugin_name=self.name, status="error", error=str(e))
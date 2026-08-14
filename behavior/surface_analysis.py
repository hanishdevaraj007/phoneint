"""
phoneint_core.plugins.surface_analysis

Migrated from the original phoneINT.py osint_hints().
Unlike validation/geolocation, this plugin doesn't hit a new source —
it derives flags from validation's output, so it declares that
dependency and reads it from `context` instead of recomputing anything.
"""

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase


class SurfaceAnalysisPlugin(PluginBase):
    name = "surface_analysis"
    requires_network = False
    depends_on = ["validation"]

    def run(self, parsed_number, context=None) -> PluginResult:
        context = context or {}
        validation_result = context.get("validation")

        if validation_result is None or validation_result.status != "ok":
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error="surface_analysis requires a successful 'validation' result",
            )

        metadata = validation_result.data
        hints = []

        if metadata.get("Number Type") == "VoIP":
            hints.append("VoIP number detected — may indicate anonymization or virtual SIM usage")
        if metadata.get("Carrier") == "Unknown":
            hints.append("Carrier unresolved — possible MVNO, eSIM, or number porting")
        if metadata.get("Region") == "Unknown":
            hints.append("Region unresolved — possible satellite or non-geographic number")

        if not hints:
            hints.append("No anomalies detected")

        return PluginResult(plugin_name=self.name, status="ok", data={"hints": hints})
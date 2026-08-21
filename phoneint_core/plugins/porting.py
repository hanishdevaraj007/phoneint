"""
phoneint_core.plugins.porting

True carrier-porting-history APIs (Twilio Lookup, etc.) are paid-only,
so this plugin uses a real, key-free-if-you-already-have-reputation-set-up
heuristic instead:

    phonenumbers' `carrier` module ships a static, periodically-updated
    range database. AbstractAPI's `reputation` plugin queries a live
    carrier registry. If the two disagree, the number has likely been
    ported to a different carrier since the static DB snapshot — that
    disagreement IS the signal, not a guess.

Depends on both `validation` (static carrier) and `reputation` (live
carrier). If `reputation` was skipped (no API key), this plugin skips
too, since it has nothing to compare against.
"""

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase


def _normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


class PortingPlugin(PluginBase):
    name = "porting"
    requires_network = False  # relies on data other plugins already fetched
    depends_on = ["validation", "reputation"]

    def run(self, parsed_number, context=None) -> PluginResult:
        context = context or {}
        validation_result = context.get("validation")
        reputation_result = context.get("reputation")

        if not validation_result or validation_result.status != "ok":
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error="porting requires a successful 'validation' result",
            )

        if not reputation_result or reputation_result.status != "ok":
            return PluginResult(
                plugin_name=self.name,
                status="skipped",
                error=(
                    "porting needs live carrier data from 'reputation' "
                    "(set ABSTRACTAPI_PHONE_KEY to enable)"
                ),
            )

        static_carrier = validation_result.data.get("Carrier", "Unknown")
        live_carrier = reputation_result.data.get("Carrier", "Unknown")

        if static_carrier in ("Unknown", "") or live_carrier in ("Unknown", ""):
            return PluginResult(
                plugin_name=self.name,
                status="ok",
                data={
                    "static_carrier": static_carrier,
                    "live_carrier": live_carrier,
                    "likely_ported": "Inconclusive",
                    "note": "One or both carrier sources are unresolved.",
                },
            )

        likely_ported = _normalize(static_carrier) != _normalize(live_carrier)

        return PluginResult(
            plugin_name=self.name,
            status="ok",
            data={
                "static_carrier": static_carrier,
                "live_carrier": live_carrier,
                "likely_ported": "Yes" if likely_ported else "No",
                "note": (
                    "Static and live carrier records disagree — number was "
                    "likely ported since the offline database snapshot."
                    if likely_ported
                    else "Static and live carrier records agree."
                ),
            },
        )
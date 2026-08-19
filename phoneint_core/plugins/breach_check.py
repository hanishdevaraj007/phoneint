"""
phoneint_core.plugins.breach_check

Checks HaveIBeenPwned for breach exposure tied to the number.
HIBP no longer offers a free tier — this plugin requires the user to
supply their own API key via the HIBP_API_KEY environment variable.
If it's not set, the plugin returns status="skipped" instead of
failing the whole investigation, so PhoneINT still works fully
without this key configured.

Get a key at: https://haveibeenpwned.com/API/Key
"""

import os
import requests

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase

HIBP_API_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{account}"


class BreachCheckPlugin(PluginBase):
    name = "breach_check"
    requires_network = True
    depends_on = ["validation"]

    def run(self, parsed_number, context=None) -> PluginResult:
        api_key = os.environ.get("HIBP_API_KEY")

        if not api_key:
            return PluginResult(
                plugin_name=self.name,
                status="skipped",
                error="HIBP_API_KEY not set — get one at https://haveibeenpwned.com/API/Key",
            )

        context = context or {}
        validation_result = context.get("validation")
        if not validation_result or validation_result.status != "ok":
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error="breach_check requires a successful 'validation' result",
            )

        e164 = validation_result.data.get("E164 Format")

        headers = {
            "hibp-api-key": api_key,
            "user-agent": "PhoneINT-OSINT-Tool",
        }

        try:
            response = requests.get(
                HIBP_API_URL.format(account=e164),
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            return PluginResult(plugin_name=self.name, status="error", error=f"Network error: {e}")

        if response.status_code == 404:
            return PluginResult(
                plugin_name=self.name,
                status="ok",
                data={"breaches_found": 0, "breaches": []},
            )

        if response.status_code == 401:
            return PluginResult(
                plugin_name=self.name, status="error", error="HIBP rejected the API key (401)"
            )

        if response.status_code == 429:
            return PluginResult(
                plugin_name=self.name, status="error", error="Rate limited by HIBP (429) — try again shortly"
            )

        if response.status_code != 200:
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"HTTP {response.status_code} from HIBP API",
            )

        breaches = response.json()
        names = [b.get("Name", "Unknown") for b in breaches]

        return PluginResult(
            plugin_name=self.name,
            status="ok",
            data={"breaches_found": len(names), "breaches": names},
        )
"""
phoneint_core.plugins.reputation

AbstractAPI restructured this product: the old "Phone Validation API"
(phonevalidation.abstractapi.com) has been superseded on newer accounts
by "Phone Intelligence" (phoneintelligence.abstractapi.com), which
returns a richer, differently-shaped payload — carrier, location,
VoIP/risk flags, and even breach fields (breach data is typically
gated to paid plans and comes back null on the free tier, which is
why PhoneINT still runs its own breach_check plugin separately).

Requires ABSTRACTAPI_PHONE_KEY environment variable. Skips gracefully
(status="skipped") if not configured.

Get a free key at: https://www.abstractapi.com/api/phone-validation-api
(the dashboard may label it "Phone Intelligence" depending on when
your account was created — use whichever key/product page it shows
under "Phone" in your AbstractAPI dashboard.)
"""

import os
import requests

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase

ABSTRACT_API_URL = "https://phoneintelligence.abstractapi.com/v1/"


class ReputationPlugin(PluginBase):
    name = "reputation"
    requires_network = True
    depends_on = ["validation"]

    def run(self, parsed_number, context=None) -> PluginResult:
        api_key = os.environ.get("ABSTRACTAPI_PHONE_KEY")

        if not api_key:
            return PluginResult(
                plugin_name=self.name,
                status="skipped",
                error=(
                    "ABSTRACTAPI_PHONE_KEY not set — get a free key at "
                    "https://www.abstractapi.com/api/phone-validation-api"
                ),
            )

        context = context or {}
        validation_result = context.get("validation")
        if not validation_result or validation_result.status != "ok":
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error="reputation requires a successful 'validation' result",
            )

        e164 = validation_result.data.get("E164 Format")

        try:
            response = requests.get(
                ABSTRACT_API_URL,
                params={"api_key": api_key, "phone": e164},
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            return PluginResult(plugin_name=self.name, status="error", error=f"Network error: {e}")

        if response.status_code == 401:
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=(
                    "AbstractAPI rejected the key (401). Check your dashboard at "
                    "abstractapi.com to confirm the key is Active and matches the "
                    "'Phone' product, not a different API."
                ),
            )

        if response.status_code == 422:
            body_preview = response.text[:200].replace("\n", " ")
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"AbstractAPI rejected the phone number format (422). Body: {body_preview}",
            )

        if response.status_code != 200:
            body_preview = response.text[:200].replace("\n", " ")
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"HTTP {response.status_code} from AbstractAPI. Body: {body_preview}",
            )

        try:
            payload = response.json()
        except ValueError as e:
            return PluginResult(
                plugin_name=self.name, status="error", error=f"Could not parse AbstractAPI response: {e}"
            )

        carrier_block    = payload.get("phone_carrier") or {}
        location_block   = payload.get("phone_location") or {}
        validation_block = payload.get("phone_validation") or {}
        risk_block        = payload.get("phone_risk") or {}
        breach_block      = payload.get("phone_breaches") or {}

        data = {
            "Valid (per AbstractAPI)": validation_block.get("is_valid"),
            "Line Status":             validation_block.get("line_status", "Unknown"),
            "Is VoIP":                 validation_block.get("is_voip"),
            "Carrier":                 carrier_block.get("name", "Unknown"),
            "Line Type":               carrier_block.get("line_type", "Unknown"),
            "Country":                 location_block.get("country_name", "Unknown"),
            "Region":                  location_block.get("region", "Unknown"),
            "City":                    location_block.get("city", "Unknown"),
            "Timezone":                location_block.get("timezone", "Unknown"),
            "Risk Level":              risk_block.get("risk_level", "Unknown"),
            "Is Disposable":           risk_block.get("is_disposable"),
            "Abuse Detected":          risk_block.get("is_abuse_detected"),
        }

        # Only include breach fields if AbstractAPI actually populated them
        # (typically null on free-tier accounts, gated to paid plans).
        if breach_block.get("total_breaches") is not None:
            data["Total Breaches (AbstractAPI)"] = breach_block.get("total_breaches")
            data["First Breach Date"] = breach_block.get("date_first_breached")
            data["Last Breach Date"] = breach_block.get("date_last_breached")

        return PluginResult(plugin_name=self.name, status="ok", data=data)
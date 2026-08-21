"""
phoneint_core.plugins.validation

Migrated from the original phoneINT.py extract_metadata().
No behavior change — just moved behind the plugin interface.
"""

import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase

NUM_TYPE_MAP = {
    PhoneNumberType.MOBILE:               "Mobile",
    PhoneNumberType.FIXED_LINE:           "Fixed Line",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
    PhoneNumberType.TOLL_FREE:            "Toll Free",
    PhoneNumberType.PREMIUM_RATE:         "Premium Rate",
    PhoneNumberType.VOIP:                 "VoIP",
    PhoneNumberType.UNKNOWN:              "Unknown",
}


class ValidationPlugin(PluginBase):
    name = "validation"
    requires_network = False

    def run(self, parsed_number, context=None) -> PluginResult:
        ntype = number_type(parsed_number)

        data = {
            "E164 Format":     phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164),
            "International":   phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "National":        phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL),
            "Country Code":    f"+{parsed_number.country_code}",
            "National Number": str(parsed_number.national_number),
            "Region":          geocoder.description_for_number(parsed_number, "en") or "Unknown",
            "Carrier":         carrier.name_for_number(parsed_number, "en") or "Unknown",
            "Timezones":       ", ".join(timezone.time_zones_for_number(parsed_number)) or "Unknown",
            "Number Type":     NUM_TYPE_MAP.get(ntype, "Unknown"),
            "Is Valid":        str(phonenumbers.is_valid_number(parsed_number)),
            "Is Possible":     str(phonenumbers.is_possible_number(parsed_number)),
        }

        return PluginResult(plugin_name=self.name, status="ok", data=data)

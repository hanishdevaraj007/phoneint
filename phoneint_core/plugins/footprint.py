"""
phoneint_core.plugins.footprint

Generates reverse-lookup and social-platform search URLs for the target
number. This does NOT scrape or authenticate against any platform — it
only builds the same search/click-to-chat URLs a human would construct
manually. That keeps this plugin legal and key-free, while still giving
an investigator a fast set of pivot points to check by hand.
"""

import phonenumbers

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase


class FootprintPlugin(PluginBase):
    name = "footprint"
    requires_network = False  # only builds URLs, doesn't fetch them
    depends_on = ["validation"]

    def run(self, parsed_number, context=None) -> PluginResult:
        context = context or {}
        e164 = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        digits_only = e164.replace("+", "")
        national = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL
        )

        links = {
            "Google Search (E164)":       f"https://www.google.com/search?q=%22{e164}%22",
            "Google Search (National)":   f"https://www.google.com/search?q=%22{national}%22",
            "WhatsApp Click-to-Chat":     f"https://wa.me/{digits_only}",
            "Telegram (by number)":       f"https://t.me/+{digits_only}",
            "Truecaller Search":          f"https://www.truecaller.com/search/in/{digits_only}",
            "Facebook Search":            f"https://www.facebook.com/search/top/?q={e164}",
            "Sync.me Lookup":             f"https://sync.me/search/?number={digits_only}",
        }

        return PluginResult(
            plugin_name=self.name,
            status="ok",
            data={
                "note": "Generated search/pivot URLs only — no data was fetched or scraped.",
                "links": links,
            },
        )
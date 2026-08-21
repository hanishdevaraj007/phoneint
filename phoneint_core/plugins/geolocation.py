"""
phoneint_core.plugins.geolocation

restcountries.com's free v3.1 API was fully deprecated (it now returns
a JSON:API-style error body instead of country data), and its
replacement v5 requires a paid API key. This plugin now uses
countries.dev instead — a free, keyless, drop-in country-data API with
the same information (capital, region, coordinates aren't included by
countries.dev, so Maps Link is built from a search query instead of
exact lat/lng — still opens the right place on the map).

No API key required. No signup required.
Docs: https://countries.dev/docs
"""

import phonenumbers
import requests

from phoneint_core.models import PluginResult
from phoneint_core.plugins.base import PluginBase


class GeolocationPlugin(PluginBase):
    name = "geolocation"
    requires_network = True

    def run(self, parsed_number, context=None) -> PluginResult:
        region_code = phonenumbers.region_code_for_number(parsed_number)

        if not region_code:
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error="Could not determine region code for number",
            )

        url = f"https://countries.dev/alpha/{region_code}"
        headers = {"User-Agent": "Mozilla/5.0 (PhoneINT-OSINT-Tool)"}

        try:
            response = requests.get(url, headers=headers, timeout=8)
        except requests.exceptions.RequestException as e:
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"Network error reaching countries.dev: {type(e).__name__}: {e}",
            )

        if response.status_code != 200:
            body_preview = response.text[:200].replace("\n", " ")
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"HTTP {response.status_code} from countries.dev. Body: {body_preview}",
            )

        try:
            country_data = response.json()
        except ValueError as e:
            body_preview = response.text[:200].replace("\n", " ")
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"Could not parse countries.dev response ({type(e).__name__}: {e}). Body: {body_preview}",
            )

        # countries.dev returns a single flat object (not a list), unlike
        # the old restcountries.com v3.1 shape — no [0] indexing needed.
        country_name = country_data.get("name", "Unknown")
        capital = country_data.get("capital", "Unknown")
        population = country_data.get("population", "Unknown")
        calling_codes = country_data.get("callingCodes", [])

        # countries.dev doesn't return lat/lng, so build a Maps search
        # link from the country name instead of exact coordinates.
        maps_link = (
            f"https://www.google.com/maps/search/?api=1&query={country_name.replace(' ', '+')}"
            if country_name != "Unknown" else "Unavailable"
        )

        data = {
            "Country":       country_name,
            "Capital":       capital,
            "Region":        country_data.get("region", "Unknown"),
            "Subregion":     country_data.get("subregion", "Unknown"),
            "Population":    f"{population:,}" if isinstance(population, int) else population,
            "Area (km2)":    country_data.get("area", "Unknown"),
            "Calling Code":  ", ".join(f"+{c}" for c in calling_codes) if calling_codes else "Unknown",
            "Top-Level Domain": ", ".join(country_data.get("topLevelDomain", [])) or "Unknown",
            "Maps Link":     maps_link,
        }

        return PluginResult(plugin_name=self.name, status="ok", data=data)
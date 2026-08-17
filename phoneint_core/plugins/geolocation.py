"""
phoneint_core.plugins.geolocation

Migrated from the original phoneINT.py geolocate().
No behavior change — just moved behind the plugin interface.
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

        url = f"https://restcountries.com/v3.1/alpha/{region_code}"

        try:
            response = requests.get(url, timeout=8)
        except requests.exceptions.RequestException as e:
            return PluginResult(plugin_name=self.name, status="error", error=f"Network error: {e}")

        if response.status_code != 200:
            return PluginResult(
                plugin_name=self.name,
                status="error",
                error=f"HTTP {response.status_code} from restcountries API",
            )

        country_data = response.json()[0]
        latlng = country_data.get("latlng", [None, None])
        capital = country_data.get("capital", ["Unknown"])[0]
        population = country_data.get("population", "Unknown")

        data = {
            "Country":    country_data.get("name", {}).get("common", "Unknown"),
            "Capital":    capital,
            "Region":     country_data.get("region", "Unknown"),
            "Subregion":  country_data.get("subregion", "Unknown"),
            "Latitude":   latlng[0] if latlng else "Unknown",
            "Longitude":  latlng[1] if latlng else "Unknown",
            "Population": f"{population:,}" if isinstance(population, int) else population,
            "Flag":       country_data.get("flag", ""),
            "Maps Link":  f"https://www.google.com/maps?q={latlng[0]},{latlng[1]}" if latlng[0] else "Unavailable",
        }

        return PluginResult(plugin_name=self.name, status="ok", data=data)
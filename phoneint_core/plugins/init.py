"""
phoneint_core.plugins

PLUGIN_REGISTRY is the single list the engine reads to know what to run.
To add a new plugin: import it here and add an instance to the list.
Nothing in engine.py needs to change.
"""

from phoneint_core.plugins.validation import ValidationPlugin
from phoneint_core.plugins.geolocation import GeolocationPlugin
from phoneint_core.plugins.surface_analysis import SurfaceAnalysisPlugin

PLUGIN_REGISTRY = [
    ValidationPlugin(),
    GeolocationPlugin(),
    SurfaceAnalysisPlugin(),
    # Tier 2 additions will slot in here: BreachCheckPlugin(), ReputationPlugin(),
    # FootprintPlugin(), PortingPlugin() ...
]
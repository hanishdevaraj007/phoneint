"""
phoneint_core.plugins

PLUGIN_REGISTRY is the single list the engine reads to know what to run.
To add a new plugin: import it here and add an instance to the list.
Nothing in engine.py needs to change.
"""

from phoneint_core.plugins.validation import ValidationPlugin
from phoneint_core.plugins.geolocation import GeolocationPlugin
from phoneint_core.plugins.surface_analysis import SurfaceAnalysisPlugin
from phoneint_core.plugins.footprint import FootprintPlugin
from phoneint_core.plugins.breach_check import BreachCheckPlugin
from phoneint_core.plugins.reputation import ReputationPlugin
from phoneint_core.plugins.porting import PortingPlugin

PLUGIN_REGISTRY = [
    ValidationPlugin(),
    GeolocationPlugin(),
    SurfaceAnalysisPlugin(),
    FootprintPlugin(),
    ReputationPlugin(),   # must run before PortingPlugin — engine orders by depends_on
    BreachCheckPlugin(),
    PortingPlugin(),
    # Tier 2 complete. Tier 3 (correlation engine, scoring, plugin marketplace) next.
]

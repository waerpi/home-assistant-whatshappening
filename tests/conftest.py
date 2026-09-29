"""Loads the modules under test directly from disk.

The prediction maths and the event model deliberately have no Home Assistant
imports, so the tests can exercise them without a full HA install. Loading by
path keeps the package's `__init__` (which does import HA) out of the way.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "whatshappening"


def load(name: str):
    """Import a single module file from the integration."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, COMPONENT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

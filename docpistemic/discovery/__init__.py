"""
Discovery module - Auto-detect project features.

Supports:
- CLI frameworks: argparse, click, typer, fire
- Web frameworks: FastAPI, Flask, Django
- Core modules: classes, functions, constants
- Configuration: env vars, config files
"""

from .api_discovery import APIDiscovery
from .cli_discovery import CLIDiscovery
from .config_discovery import ConfigDiscovery
from .module_discovery import ModuleDiscovery

__all__ = [
    "CLIDiscovery",
    "ModuleDiscovery",
    "APIDiscovery",
    "ConfigDiscovery",
]

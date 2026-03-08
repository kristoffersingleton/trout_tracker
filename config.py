"""
Load home location from config.yaml, falling back to config.example.yaml.
"""

import yaml
from pathlib import Path

_BASE = Path(__file__).parent

def _load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)["home"]

def load_home_location():
    for filename in ("config.yaml", "config.example.yaml"):
        path = _BASE / filename
        if path.exists():
            try:
                return _load_yaml(path)
            except Exception as e:
                print(f"Warning: could not load {filename} ({e}), trying next.")
    raise FileNotFoundError("No config.yaml or config.example.yaml found.")

HOME_LOCATION = load_home_location()

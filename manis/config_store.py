"""Persist tunnel configurations to a JSON file."""

import json
import os
from pathlib import Path
from typing import Optional

from .models import TunnelConfig


CONFIG_DIR = Path.home() / ".manis"
CONFIG_FILE = CONFIG_DIR / "tunnels.json"
SSH_CONFIG_CACHE = CONFIG_DIR / "ssh_config_cache.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_tunnels() -> list[TunnelConfig]:
    """Load all tunnel configurations."""
    if not CONFIG_FILE.exists():
        return []
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return [TunnelConfig.from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_tunnels(tunnels: list[TunnelConfig]):
    """Save tunnel configurations."""
    ensure_config_dir()
    data = [t.to_dict() for t in tunnels]
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_tunnel(tunnel: TunnelConfig) -> list[TunnelConfig]:
    """Add a tunnel and return updated list."""
    tunnels = load_tunnels()
    # Remove existing tunnel with same name
    tunnels = [t for t in tunnels if t.name != tunnel.name]
    tunnels.append(tunnel)
    save_tunnels(tunnels)
    return tunnels


def remove_tunnel(name: str) -> list[TunnelConfig]:
    """Remove a tunnel by name."""
    tunnels = load_tunnels()
    tunnels = [t for t in tunnels if t.name != name]
    save_tunnels(tunnels)
    return tunnels


def update_tunnel(name: str, updates: dict) -> Optional[TunnelConfig]:
    """Update a tunnel's fields."""
    tunnels = load_tunnels()
    for t in tunnels:
        if t.name == name:
            for k, v in updates.items():
                if hasattr(t, k):
                    setattr(t, k, v)
            save_tunnels(tunnels)
            return t
    return None

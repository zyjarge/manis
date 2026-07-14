"""Parse ~/.ssh/config files to extract host entries."""

import os
import re
from pathlib import Path
from typing import Optional

from .models import SSHHost


def parse_ssh_config(path: Optional[str] = None) -> list[SSHHost]:
    """Parse SSH config file and return list of SSHHost entries."""
    path = path or os.path.expanduser("~/.ssh/config")
    config_file = Path(path)
    if not config_file.exists():
        return []

    hosts: list[SSHHost] = []
    current_host: Optional[str] = None
    current_props: dict = {}

    with open(config_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Match "Host pattern" lines
            m = re.match(r"^Host\s+(.+)$", line, re.IGNORECASE)
            if m:
                # Save previous host
                if current_host and not _is_wildcard(current_host):
                    hosts.append(_make_host(current_host, current_props))
                current_host = m.group(1).strip()
                current_props = {}
                continue

            # Match property lines
            m = re.match(r"^\s*(HostName|User|Port|IdentityFile)\s+(.+)$", line, re.IGNORECASE)
            if m:
                key = m.group(1).lower()
                val = m.group(2).strip()
                # Handle quoted values
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                current_props[key] = val

    # Save last host
    if current_host and not _is_wildcard(current_host):
        hosts.append(_make_host(current_host, current_props))

    return hosts


def _is_wildcard(host: str) -> bool:
    """Check if a Host pattern contains wildcards."""
    return "*" in host or "?" in host


def _make_host(pattern: str, props: dict) -> SSHHost:
    # Expand ~ in IdentityFile
    identity_file = props.get("identityfile")
    if identity_file:
        identity_file = os.path.expanduser(identity_file)

    port = None
    if "port" in props:
        try:
            port = int(props["port"])
        except ValueError:
            pass

    return SSHHost(
        host=pattern,
        hostname=props.get("hostname"),
        user=props.get("user"),
        port=port,
        identity_file=identity_file,
    )

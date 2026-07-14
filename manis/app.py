"""manis - main application entry with pywebview."""

import os
import threading
import webview

from .models import TunnelConfig, ForwardRule
from .config_store import load_tunnels, save_tunnels, add_tunnel, remove_tunnel
from .ssh_config_parser import parse_ssh_config
from .tunnel_manager import TunnelManager

_manager = TunnelManager()


class API:
    """JavaScript-bridge API exposed to the webview."""

    def list_tunnels(self) -> list[dict]:
        """Return all tunnels with running status."""
        tunnels = load_tunnels()
        result = []
        for t in tunnels:
            d = t.to_dict()
            d["running"] = _manager.is_running(t.name)
            result.append(d)
        return result

    def toggle_tunnel(self, name: str) -> str:
        """Start or stop a tunnel. Returns status message."""
        tunnels = load_tunnels()
        tunnel = next((t for t in tunnels if t.name == name), None)
        if not tunnel:
            return f"❌ 找不到隧道 '{name}'"

        if _manager.is_running(name):
            ok, msg = _manager.stop(name)
        else:
            ok, msg = _manager.start(tunnel)
        return msg

    def delete_tunnel(self, name: str) -> str:
        """Delete a tunnel configuration."""
        # Stop if running
        if _manager.is_running(name):
            _manager.stop(name)
        remove_tunnel(name)
        return f"🗑️  '{name}' 已删除"

    def save_tunnel(self, data: dict) -> str:
        """Create or update a tunnel."""
        old_name = data.pop("old_name", None)

        # If renaming, remove old config
        if old_name and old_name != data.get("name"):
            if _manager.is_running(old_name):
                _manager.stop(old_name)
            remove_tunnel(old_name)

        forwards = []
        for f in data.get("forwards", []):
            forwards.append(ForwardRule(
                local_port=int(f["local_port"]),
                remote_host=f["remote_host"],
                remote_port=int(f["remote_port"]),
            ))

        tunnel = TunnelConfig(
            name=data["name"],
            host=data["host"],
            user=data.get("user") or None,
            port=data.get("port") or None,
            identity_file=data.get("identity_file") or None,
            extra_args=data.get("extra_args", ""),
            tunnel_type=data.get("tunnel_type", "local"),
            forwards=forwards,
        )
        add_tunnel(tunnel)
        return f"✅ 隧道 '{tunnel.name}' 已保存"

    def get_ssh_hosts(self) -> list[dict]:
        """Return parsed SSH config hosts."""
        hosts = parse_ssh_config()
        result = []
        for h in hosts:
            d = h.__dict__.copy()
            d["display_name"] = h.display_name
            result.append(d)
        return result


def _find_html_path() -> str:
    """Locate the web/index.html file in both dev and bundled modes."""
    import sys

    # Bundled app: file lives in Resources/web/
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else None
        if bundle_dir:
            path = os.path.join(bundle_dir, "web", "index.html")
            if os.path.exists(path):
                return path
        # py2app structure: Resources/lib/pythonX.Y/web/
        app_root = os.path.dirname(os.path.dirname(sys.executable))
        candidates = [
            os.path.join(app_root, "Resources", "web", "index.html"),
            os.path.join(os.path.dirname(sys.executable), "..", "Resources", "web", "index.html"),
            os.path.join(os.path.dirname(sys.executable), "web", "index.html"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.abspath(path)

    # Dev mode: relative to this file
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")


def run():
    html_path = _find_html_path()
    api = API()

    # Pre-clean stale PIDs on startup
    _manager._cleanup_stale_pids()

    window = webview.create_window(
        title="manis - SSH Tunnel Manager",
        url=f"file://{html_path}",
        js_api=api,
        width=800,
        height=600,
        min_size=(600, 400),
        resizable=True,
        text_select=True,
    )
    webview.start(
        debug=True,       # Enable dev tools
    )


if __name__ == "__main__":
    run()

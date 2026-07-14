# manis

> Cross-platform SSH tunnel manager with a native web UI.

manis helps you manage SSH port-forwarding tunnels from your Mac menu
bar (or any other platform with a desktop browser). Click once to
open, click again to close — no more typing `ssh -L ...` in your
terminal every time.

![manis screenshot](manis/web/screenshot.png)

---

## ✨ Features

- **One-click on/off** — menu bar / window buttons start and stop tunnels instantly
- **Multiple tunnels, one place** — manage as many forwarding rules as you need
- **SSH Config import** — read your `~/.ssh/config` Host entries with one click
- **Persistent processes** — tunnels survive `manis` exit (PID files in `~/.manis/pids/`)
- **CLI mode** — `manis start Oracle` works from your shell too
- **Cross-platform** — runs on macOS, Linux, Windows (Python + pywebview)
- **Intel-friendly** — pure Python, no Apple Silicon requirement

---

## 📦 Installation

### From source (development)

```bash
git clone https://github.com/yourname/manis.git
cd manis
uv sync
uv run python3 -m manis          # launch GUI
```

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

### As a macOS .app (packaged)

```bash
uv run python3 setup.py py2app
open dist/manis.app
```

The standalone `.app` is fully self-contained and can be dragged into
`/Applications/`. See [PACKAGING.md](PACKAGING.md) for details on
building `.dmg` installers, code signing, and notarization.

### CLI-only install

```bash
uv tool install git+https://github.com/yourname/manis.git
manis list
```

---

## 🚀 Quick start

### 1. Launch the GUI

```bash
uv run python3 -m manis
```

A native window opens with your configured tunnels. From there you can:

- **➕ New tunnel** — fill in name, jump host, port mappings
- **📋 Import from SSH Config** — pick from your existing `~/.ssh/config`
- **▶/⏹** — toggle each tunnel on/off

### 2. Add your first tunnel (CLI)

```bash
manis add                          # adds a default Oracle tunnel
manis list                         # verify
manis start Oracle                 # open the tunnel
```

### 3. Configure Oracle access

```bash
manis add
# Edit ~/.manis/tunnels.json:
# {
#   "name": "Oracle",
#   "host": "work",                    # SSH jump host alias
#   "forwards": [{
#     "local_port": 15210,
#     "remote_host": "10.0.125.35",
#     "remote_port": 1521
#   }]
# }

manis start Oracle
# Connect via localhost:15210
sqlplus BIDWDB/BIDWDB@localhost:15210/ORAPDB19
```

---

## 📋 CLI reference

```
manis                Launch GUI window
manis list           List all configured tunnels with status
manis start <name>   Start a tunnel
manis stop  <name>   Stop a tunnel
manis stop-all       Stop all running tunnels
manis --help         Show this help
```

---

## ⚙️ Configuration

### Tunnel definitions

Stored in `~/.manis/tunnels.json`:

```json
{
  "name": "Oracle",
  "host": "work",
  "user": null,
  "port": null,
  "identity_file": null,
  "extra_args": "",
  "tunnel_type": "local",
  "forwards": [
    {
      "local_port": 15210,
      "remote_host": "10.0.125.35",
      "remote_port": 1521
    }
  ],
  "auto_connect": false,
  "enabled": true
}
```

### Runtime state

Active tunnel PIDs are stored in `~/.manis/pids/<name>.pid`.
Stale PIDs (process no longer running) are auto-cleaned on startup.

### Multi-forward example

```json
{
  "name": "dev-cluster",
  "host": "work",
  "tunnel_type": "local",
  "forwards": [
    {"local_port": 8080,  "remote_host": "10.0.0.10", "remote_port": 80},
    {"local_port": 3306,  "remote_host": "10.0.0.10", "remote_port": 3306},
    {"local_port": 5432,  "remote_host": "10.0.0.11", "remote_port": 5432}
  ]
}
```

One click opens all three.

---

## 🏗️ Architecture

```
manis/
├── pyproject.toml             # uv/pip project config
├── setup.py                   # py2app .app bundle config
├── main.py                    # Bundled .app entry point
├── PACKAGING.md               # Detailed packaging guide
├── manis/
│   ├── __init__.py
│   ├── __main__.py            # CLI entry (manis <command>)
│   ├── app.py                 # pywebview window + API bridge
│   ├── models.py              # TunnelConfig, ForwardRule, SSHHost
│   ├── config_store.py        # JSON persistence
│   ├── ssh_config_parser.py   # ~/.ssh/config reader
│   ├── tunnel_manager.py      # SSH subprocess lifecycle
│   └── web/
│       └── index.html         # UI (vanilla HTML/CSS/JS)
```

### How the SSH tunnel actually works

```
┌─────────┐         ┌─────────────┐         ┌──────────────┐
│   App   │ ──SSH──>│ work (jump) │ ──TCP──>│ Oracle 1521  │
│ :15210  │  tunnel │ 10.0.125.43 │         │ 10.0.125.35  │
└─────────┘         └─────────────┘         └──────────────┘
```

`manis` spawns: `ssh -N -L 15210:10.0.125.35:1521 work` with
`ServerAliveInterval=30` and `ExitOnForwardFailure=yes`. The process
runs in its own session, so closing the GUI doesn't kill the tunnel.

### Why pywebview?

- **Native window** — uses the system's WebKit (WKWebView on macOS),
  WebView2 (Windows), or GTK WebKit (Linux). No Electron bloat.
- **JS ↔ Python bridge** — `window.pywebview.api` lets the UI call
  Python methods directly. No HTTP server needed.
- **Tiny dependency footprint** — pure Python + system WebKit.

---

## 🔌 Use cases

### Access internal databases

```
Oracle:  localhost:15210  →  10.0.125.35:1521
MySQL:   localhost:13306  →  10.0.0.60:3306
PG:      localhost:15432  →  10.0.0.60:5432
```

### Internal web UIs

```
Jenkins: localhost:18080  →  10.0.126.66:8080
Grafana:  localhost:13000  →  10.0.0.30:3000
```

### RDP / SSH into internal hosts

```
RDP:     localhost:13389  →  10.0.0.100:3389
```

### SOCKS proxy

Set `tunnel_type: "dynamic"` to get a `ssh -D` SOCKS proxy on
`localhost:1080`.

---

## 🛠️ Development

```bash
# Install dev deps
uv sync

# Run from source (auto-reload not supported)
uv run python3 -m manis

# Build .app bundle
uv run python3 setup.py py2app

# Verify the bundle
open dist/manis.app
```

### Module overview

| Module                  | Purpose                                            |
|-------------------------|----------------------------------------------------|
| `models.py`             | Dataclasses for tunnels, forwards, SSH hosts       |
| `config_store.py`       | JSON persistence at `~/.manis/tunnels.json`        |
| `ssh_config_parser.py`  | Parse `~/.ssh/config` Host entries                 |
| `tunnel_manager.py`     | Spawn / stop / monitor SSH subprocesses            |
| `app.py`                | pywebview window + `API` class exposed to JS       |
| `web/index.html`        | Single-file UI (no build step)                     |

### Adding a new field

1. Add field to `TunnelConfig` dataclass in `models.py`
2. Update `to_dict()` / `from_dict()` if needed
3. Add `<input>` to the modal in `web/index.html`
4. Pass through `API.save_tunnel()` in `app.py`

---

## 📋 Requirements

- Python 3.10+
- macOS 11.0+ (for `.app` build)
- `pywebview>=4.0`
- `ssh` (pre-installed on macOS/Linux)

---

## 🐛 Troubleshooting

### "Pywebview fails to start"

Make sure you're running from a **GUI terminal session**, not over
SSH without forwarding. On macOS, launch Terminal.app first.

### "Address already in use"

Another tunnel (or a leftover SSH process) is using the local port.

```bash
lsof -i :15210
# kill the PID, then: manis stop Oracle
```

### "Connection refused"

The jump host can't reach the target. Test manually:

```bash
ssh work "nc -zv 10.0.125.35 1521"
```

### Tunnel dies when GUI closes

manis uses `start_new_session=True` and PID files — tunnels should
survive GUI exit. If they don't, check `~/.manis/pids/` for stale
PID files:

```bash
ls -la ~/.manis/pids/
cat ~/.manis/pids/Oracle.pid    # check the PID
ps -p $(cat ~/.manis/pids/Oracle.pid)
```

---

## 📄 License

MIT. See [LICENSE](LICENSE).

## 🙏 Credits

Inspired by [TypoStudio/ssh-tunnel-for-macos](https://github.com/TypoStudio/ssh-tunnel-for-macos)
(macOS-only SwiftUI app, GPLv3). This project re-implements the core
tunnel-management ideas in Python + pywebview so it works on any
platform and architecture (including Intel Macs).
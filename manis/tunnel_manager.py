"""Manage SSH tunnel subprocesses."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from .models import TunnelConfig

PID_DIR = Path.home() / ".manis" / "pids"


def _ensure_pid_dir():
    PID_DIR.mkdir(parents=True, exist_ok=True)


def _pid_file(name: str) -> Path:
    return PID_DIR / f"{name}.pid"


def _save_pid(name: str, pid: int):
    _ensure_pid_dir()
    _pid_file(name).write_text(str(pid))


def _load_pid(name: str) -> Optional[int]:
    pid_file = _pid_file(name)
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def _remove_pid(name: str):
    pid_file = _pid_file(name)
    if pid_file.exists():
        pid_file.unlink()


def _is_pid_alive(pid: int) -> bool:
    """Check if a process with given PID is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


class TunnelManager:
    """Manages SSH tunnel subprocesses."""

    def __init__(self):
        self._processes: dict[str, subprocess.Popen] = {}
        self._cleanup_stale_pids()

    def _cleanup_stale_pids(self):
        """Remove PID files for processes that are no longer running."""
        _ensure_pid_dir()
        for pid_file in PID_DIR.glob("*.pid"):
            name = pid_file.stem
            pid = _load_pid(name)
            if pid is None or not _is_pid_alive(pid):
                _remove_pid(name)

    def start(self, tunnel: TunnelConfig) -> tuple[bool, str]:
        """Start a tunnel. Returns (success, message)."""
        # Check if already running
        existing_pid = _load_pid(tunnel.name)
        if existing_pid and _is_pid_alive(existing_pid):
            return False, f"'{tunnel.name}' 已经在运行中 (PID {existing_pid})"

        args = self._build_ssh_args(tunnel)
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent process group
            )
            self._processes[tunnel.name] = proc
            _save_pid(tunnel.name, proc.pid)
            return True, f"✅ '{tunnel.name}' 已启动 (PID {proc.pid})"
        except FileNotFoundError:
            return False, "❌ 找不到 ssh 命令，请确认已安装"
        except Exception as e:
            return False, f"❌ 启动失败: {e}"

    def stop(self, name: str) -> tuple[bool, str]:
        """Stop a running tunnel."""
        # Check PID file first
        pid = _load_pid(name)
        if pid and _is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                # Wait briefly for it to die
                for _ in range(10):
                    if not _is_pid_alive(pid):
                        break
                    time.sleep(0.1)
                else:
                    # Force kill
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
            except OSError:
                pass
            _remove_pid(name)

        # Also check in-process processes
        if name in self._processes:
            proc = self._processes[name]
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            del self._processes[name]

        _remove_pid(name)
        return True, f"⏹️  '{name}' 已停止"

    def stop_all(self):
        """Stop all running tunnels."""
        names = self.list_running()
        results = []
        for name in names:
            ok, msg = self.stop(name)
            results.append(msg)
        return results

    def is_running(self, name: str) -> bool:
        """Check if a tunnel is running (from PID file or in-memory)."""
        # Check in-memory first
        if name in self._processes:
            proc = self._processes[name]
            if proc.poll() is None:
                return True
            del self._processes[name]

        # Check PID file
        pid = _load_pid(name)
        if pid and _is_pid_alive(pid):
            return True

        return False

    def list_running(self) -> list[str]:
        """List names of all running tunnels."""
        running = []

        # Check PID files
        _ensure_pid_dir()
        for pid_file in PID_DIR.glob("*.pid"):
            name = pid_file.stem
            pid = _load_pid(name)
            if pid and _is_pid_alive(pid):
                running.append(name)

        # Add in-memory processes not in PID files
        for name, proc in list(self._processes.items()):
            if proc.poll() is None and name not in running:
                running.append(name)
            elif proc.poll() is not None:
                del self._processes[name]

        return running

    def _build_ssh_args(self, tunnel: TunnelConfig) -> list[str]:
        args = ["ssh"]

        # Add port forwarding rules
        for rule in tunnel.forwards:
            args.extend(rule.to_ssh_arg(tunnel.tunnel_type))

        # SSH options for tunnel mode - keep alive
        args.extend(["-N", "-o", "ServerAliveInterval=30",
                     "-o", "ServerAliveCountMax=3",
                     "-o", "ExitOnForwardFailure=yes"])

        # Extra args
        if tunnel.extra_args:
            args.extend(tunnel.extra_args.split())

        # Identity file
        if tunnel.identity_file:
            args.extend(["-i", os.path.expanduser(tunnel.identity_file)])

        # SSH port
        if tunnel.port:
            args.extend(["-p", str(tunnel.port)])

        # Target host
        if tunnel.user:
            args.append(f"{tunnel.user}@{tunnel.host}")
        else:
            args.append(tunnel.host)

        return args

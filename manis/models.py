"""Data models for SSH tunnel configurations."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ForwardRule:
    """A single port forwarding rule."""
    local_port: int
    remote_host: str
    remote_port: int

    def to_ssh_arg(self, tunnel_type: str = "local") -> list[str]:
        if tunnel_type == "local":
            return ["-L", f"{self.local_port}:{self.remote_host}:{self.remote_port}"]
        elif tunnel_type == "remote":
            return ["-R", f"{self.local_port}:{self.remote_host}:{self.remote_port}"]
        elif tunnel_type == "dynamic":
            return ["-D", str(self.local_port)]
        return []


@dataclass
class TunnelConfig:
    """Configuration for one SSH tunnel."""
    name: str
    host: str                # SSH host alias or user@hostname
    tunnel_type: str = "local"   # local, remote, dynamic
    forwards: list[ForwardRule] = field(default_factory=list)
    port: Optional[int] = None   # SSH port
    user: Optional[str] = None   # SSH user (override)
    identity_file: Optional[str] = None
    extra_args: str = ""         # Extra SSH arguments
    auto_connect: bool = False
    enabled: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["forwards"] = [asdict(f) for f in self.forwards]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TunnelConfig":
        forwards = [ForwardRule(**f) for f in d.get("forwards", [])]
        d["forwards"] = forwards
        return cls(**d)


@dataclass
class SSHHost:
    """An entry parsed from ~/.ssh/config."""
    host: str
    hostname: Optional[str] = None
    user: Optional[str] = None
    port: Optional[int] = None
    identity_file: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.hostname and self.user:
            return f"{self.user}@{self.hostname}"
        elif self.hostname:
            return self.hostname
        return self.host

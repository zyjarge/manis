"""Entry point for manis."""

import sys


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("--help", "-h"):
            print("manis - SSH Tunnel Manager")
            print()
            print("用法:")
            print("  manis             启动 GUI 窗口")
            print("  manis list        列出隧道")
            print("  manis start <名称> 启动隧道")
            print("  manis stop  <名称> 停止隧道")
            print("  manis stop-all    停止所有")
            print("  manis --help      帮助")
            print()
            return
        elif cmd == "list":
            from .config_store import load_tunnels
            from .tunnel_manager import TunnelManager
            tunnels = load_tunnels()
            m = TunnelManager()
            if not tunnels:
                print("没有配置的隧道")
                return
            for t in tunnels:
                status = "🟢 运行中" if m.is_running(t.name) else "⚪ 已停止"
                forwards = ", ".join(f"{f.local_port}→{f.remote_host}:{f.remote_port}" for f in t.forwards)
                print(f"  {status}  {t.name}")
                print(f"           Host: {t.host}  [{forwards}]")
            return
        elif cmd == "start":
            if len(sys.argv) < 3:
                print("用法: manis start <隧道名称>")
                return
            name = sys.argv[2]
            from .config_store import load_tunnels
            from .tunnel_manager import TunnelManager
            tunnels = load_tunnels()
            tunnel = next((t for t in tunnels if t.name == name), None)
            if not tunnel:
                print(f"❌ 找不到隧道 '{name}'")
                return
            m = TunnelManager()
            ok, msg = m.start(tunnel)
            print(msg)
            return
        elif cmd == "stop":
            if len(sys.argv) < 3:
                print("用法: manis stop <隧道名称>")
                return
            name = sys.argv[2]
            from .tunnel_manager import TunnelManager
            m = TunnelManager()
            ok, msg = m.stop(name)
            print(msg)
            return
        elif cmd == "stop-all":
            from .tunnel_manager import TunnelManager
            m = TunnelManager()
            results = m.stop_all()
            for r in results:
                print(r)
            return
        else:
            print(f"未知命令: {cmd}")
            print("用法: manis --help")
            return

    # Start GUI
    from .app import run
    run()


if __name__ == "__main__":
    main()

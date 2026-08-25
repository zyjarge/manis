# manis

> 跨平台 SSH 隧道管理器，原生网页界面。

manis 帮你从 Mac 菜单栏（或其他任何带桌面浏览器的系统）管理 SSH 端口转发隧道。
点一下打开，再点一下关闭——再也不用每次都在终端里敲 `ssh -L ...` 了。

![manis 截图](manis/web/screenshot.png)

[English version →](README.en.md)

---

## ✨ 功能特性

- **一键启停** — 菜单栏/窗口按钮即可瞬时开关隧道
- **多隧道集中管理** — 想管多少条转发规则都行
- **从 SSH Config 导入** — 一键读取 `~/.ssh/config` 里的 Host 条目
- **进程持久化** — 关闭 manis 隧道依然存活（PID 文件存放在 `~/.manis/pids/`）
- **命令行模式** — 在终端里 `manis start Oracle` 也能用
- **跨平台** — macOS、Linux、Windows 都能跑（Python + pywebview）
- **对 Intel 友好** — 纯 Python，不强求 Apple Silicon

---

## 📦 安装方式

### 从源码运行（开发模式）

```bash
git clone https://github.com/yourname/manis.git
cd manis
uv sync
uv run python3 -m manis          # 启动 GUI
```

需要 Python 3.10+ 和 [uv](https://docs.astral.sh/uv/)。

### 打包为 macOS .app（独立应用）

`.app` 包用 **PyInstaller** 构建（py2app 已弃用——它与 Python 3.12+/setuptools 80+ 不兼容）。

```bash
# 构建 .app 包（必须用 framework 版的 Python 3.13）
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  uv run --python .venv/bin/python pyinstaller \
    --noconfirm --windowed --name manis \
    --add-data "manis/web:manis/web" main.py

open dist/manis.app
```

打出来的 `.app` 完全自包含，可以直接拖进 `/Applications/`。
构建 `.dmg` 安装包、代码签名、公证等细节见 [PACKAGING.md](PACKAGING.md)。

### 仅安装 CLI

```bash
uv tool install git+https://github.com/yourname/manis.git
manis list
```

---

## 🚀 快速上手

### 1. 启动 GUI

```bash
uv run python3 -m manis
```

会弹出一个原生窗口，列出已配置的隧道。你可以：

- **➕ 新建隧道** — 填写名称、跳板机、端口映射
- **📋 从 SSH Config 导入** — 从已有的 `~/.ssh/config` 里挑
- **▶/⏹** — 单独启停每条隧道

### 2. 用 CLI 加第一条隧道

```bash
manis add                          # 加一条默认的 Oracle 隧道
manis list                         # 看看是否加成功
manis start Oracle                 # 打开隧道
```

### 3. 配置 Oracle 数据库访问

```bash
manis add
# 编辑 ~/.manis/tunnels.json:
# {
#   "name": "Oracle",
#   "host": "work",                    # SSH 跳板机别名
#   "forwards": [{
#     "local_port": 15210,
#     "remote_host": "10.0.125.35",
#     "remote_port": 1521
#   }]
# }

manis start Oracle
# 通过 localhost:15210 连
sqlplus BIDWDB/BIDWDB@localhost:15210/ORAPDB19
```

---

## 📋 命令行参考

```
manis                启动 GUI 窗口
manis list           列出所有隧道及其状态
manis start <name>   启动指定隧道
manis stop  <name>   停止指定隧道
manis stop-all       停止所有运行中的隧道
manis --help         显示帮助
```

---

## ⚙️ 配置说明

### 隧道定义

存放在 `~/.manis/tunnels.json`：

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

### 运行时状态

活跃隧道的 PID 存放在 `~/.manis/pids/<name>.pid`。
进程已不存在的过期 PID 会在启动时自动清理。

### 多端口转发示例

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

点一下三个端口同时打开。

---

## 🏗️ 架构

```
manis/
├── pyproject.toml             # uv/pip 项目配置
├── setup.py                   # py2app 配置（已弃用，见 PACKAGING.md）
├── main.py                    # 打包后 .app 的入口
├── PACKAGING.md               # 详细打包文档
├── manis/
│   ├── __init__.py
│   ├── __main__.py            # CLI 入口（manis <command>）
│   ├── app.py                 # pywebview 窗口 + API 桥接
│   ├── models.py              # TunnelConfig、ForwardRule、SSHHost
│   ├── config_store.py        # JSON 持久化
│   ├── ssh_config_parser.py   # ~/.ssh/config 解析器
│   ├── tunnel_manager.py      # SSH 子进程生命周期管理
│   └── web/
│       └── index.html         # 界面（纯 HTML/CSS/JS，无构建步骤）
```

### SSH 隧道实际工作原理

```
┌─────────┐         ┌─────────────┐         ┌──────────────┐
│   App   │ ──SSH──>│ work (跳板) │ ──TCP──>│ Oracle 1521  │
│ :15210  │  隧道   │ 10.0.125.43 │         │ 10.0.125.35  │
└─────────┘         └─────────────┘         └──────────────┘
```

`manis` 启动的命令是：`ssh -N -L 15210:10.0.125.35:1521 work`，
加上 `ServerAliveInterval=30` 和 `ExitOnForwardFailure=yes`。
进程跑在独立的 session 里，关闭 GUI 不会杀掉隧道。

### 为什么用 pywebview？

- **原生窗口** — 用系统自带的 WebKit（macOS 的 WKWebView、Windows 的 WebView2、Linux 的 GTK WebKit）。不是 Electron 那种臃肿货。
- **JS ↔ Python 桥接** — `window.pywebview.api` 让界面直接调用 Python 方法，无需 HTTP 服务。
- **依赖体积极小** — 纯 Python + 系统 WebKit。

---

## 🔌 典型用法

### 访问内网数据库

```
Oracle:  localhost:15210  →  10.0.125.35:1521
MySQL:   localhost:13306  →  10.0.0.60:3306
PG:      localhost:15432  →  10.0.0.60:5432
```

### 内网 Web 控制台

```
Jenkins: localhost:18080  →  10.0.126.66:8080
Grafana:  localhost:13000  →  10.0.0.30:3000
```

### RDP / SSH 进内网机器

```
RDP:     localhost:13389  →  10.0.0.100:3389
```

### SOCKS 代理

把 `tunnel_type` 设为 `"dynamic"`，就在 `localhost:1080` 起一个 `ssh -D` SOCKS 代理。

---

## 🛠️ 开发

```bash
# 安装开发依赖
uv sync

# 从源码运行（暂不支持热重载）
uv run python3 -m manis

# 构建 .app 包（完整命令见上面"打包为 macOS .app"小节）
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  uv run --python .venv/bin/python pyinstaller \
    --noconfirm --windowed --name manis \
    --add-data "manis/web:manis/web" main.py

# 验证打包结果
open dist/manis.app
```

> 提示：推荐用提交进仓库的 `manis.spec` + `./scripts/build.sh` 一键打包，结果更可复现。详见 [PACKAGING.md](PACKAGING.md)（含 DMG、签名、公证说明）。

### 模块概览

| 模块                  | 作用                                          |
|-------------------------|----------------------------------------------------|
| `models.py`             | 隧道、端口转发、SSH 主机 的 dataclass     |
| `config_store.py`       | JSON 持久化（`~/.manis/tunnels.json`）     |
| `ssh_config_parser.py`  | 解析 `~/.ssh/config` 里的 Host 条目         |
| `tunnel_manager.py`     | SSH 子进程的启动/停止/监控                |
| `app.py`                | pywebview 窗口 + 暴露给 JS 的 `API` 类     |
| `web/index.html`        | 单文件界面（无需构建步骤）                  |

### 新增字段怎么加

1. 在 `models.py` 的 `TunnelConfig` dataclass 里加字段
2. 必要时更新 `to_dict()` / `from_dict()`
3. 在 `web/index.html` 的弹窗里加 `<input>`
4. 在 `app.py` 的 `API.save_tunnel()` 里透传

---

## 📋 环境要求

- Python 3.10+
- macOS 11.0+（打包 .app 时需要）
- `pywebview>=4.0`
- `ssh`（macOS/Linux 自带）

---

## 🐛 故障排查

### "Pywebview 无法启动"

一定要在 **带 GUI 的终端会话** 里运行，不要在没有 X 转发的纯 SSH 会话里跑。
macOS 上请先打开 Terminal.app。

### "Address already in use"

本端口被别的隧道（或残留 SSH 进程）占用了。

```bash
lsof -i :15210
# 杀掉对应 PID，然后：manis stop Oracle
```

### "Connection refused"

跳板机到不了目标地址。手动验证一下：

```bash
ssh work "nc -zv 10.0.125.35 1521"
```

### 关闭 GUI 后隧道跟着死了

manis 用 `start_new_session=True` 和 PID 文件来保证隧道存活——按理关闭 GUI 不应该杀掉隧道。
如果发现隧道真的死了，去 `~/.manis/pids/` 看看有没有过期的 PID 文件：

```bash
ls -la ~/.manis/pids/
cat ~/.manis/pids/Oracle.pid    # 看看 PID 是几
ps -p $(cat ~/.manis/pids/Oracle.pid)
```

---

## 📄 许可证

MIT。详见 [LICENSE](LICENSE)。

## 🙏 致谢

灵感来自 [TypoStudio/ssh-tunnel-for-macos](https://github.com/TypoStudio/ssh-tunnel-for-macos)
（macOS-only SwiftUI 应用，GPLv3）。本项目用 Python + pywebview 重新实现了核心的
隧道管理思路，因此可以跑在任何平台、任何架构上（包括 Intel Mac）。
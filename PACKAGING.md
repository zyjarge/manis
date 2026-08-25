# 打包 manis 为 macOS 桌面应用

## TL;DR

```bash
./scripts/build.sh
open dist/manis.app
```

`scripts/build.sh` 会重建 venv、装依赖、跑 PyInstaller，并对产物做一次冒烟测试。详见 [§一](#一推荐脚本)。

---

## 历史背景：为什么不用 py2app 了

manis 最早用 **py2app**。它和当前生态有三重不兼容：

| Python 版本 | 问题 |
|---|---|
| 3.12 (uv 的 -none 版) | py2app 找不到 framework libpython，启动报 *"A Python runtime could not be located"* |
| 3.12 (任何 build) | py2app 0.28 的 setuptools 集成拒绝 `install_requires`，setuptools 80+ 拒绝 `setup_requires` |
| 3.13 (framework) | py2app 0.28.10 调 `subprocess.Popen(verbose=...)`，Python 3.13 移除了该 kwarg |

py2app 最后一次发版是 2023 年，作者基本停更。**manis 全面改用 PyInstaller。**

旧的 `setup.py` 仍保留以便参考，但已经不能用了——`setup_requires=["py2app"]` 在新 setuptools 下直接抛错。

---

## 一、推荐：脚本

```bash
cd ~/workspace/manis
./scripts/build.sh
```

脚本会做的事：

1. 重新创建 `.venv`（强制用 brew 的 framework 版 Python 3.13，覆盖 `.python-version` 里的 3.12）
2. 安装项目依赖 + PyInstaller
3. 清掉旧的 `build/` `dist/`
4. 跑 `pyinstaller manis.spec`
5. 启动产物做冒烟测试（开窗口 3 秒后还在 → 杀掉退出）

可调参数：

```bash
# 用别的 framework 版 Python（譬如 M1 Mac 上的 arm64 build）
PYTHON_BIN=/opt/homebrew/Cellar/python@3.13/3.13.11_1/bin/python3.13 ./scripts/build.sh
```

前置依赖：

```bash
brew install python@3.13    # framework 版 Python
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 二、手动：分步命令

如果想看每一步在干什么：

```bash
cd ~/workspace/manis

# 1. 用 framework 版 Python 建 venv（关键！uv 默认装的 -none 版打包后会启动失败）
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  uv venv --python /usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13

# 2. 装依赖 + PyInstaller
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 uv sync
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  uv pip install --python .venv/bin/python pyinstaller

# 3. 一行命令打包（不推荐，分散维护成本——改用 manis.spec）
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  .venv/bin/pyinstaller --noconfirm --windowed --name manis \
    --add-data "manis/web:manis/web" main.py

# 或者用提交进仓库的 spec 文件（推荐）
UV_PYTHON=/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  .venv/bin/pyinstaller --noconfirm manis.spec
```

产物 `dist/manis.app` 完全可以拖进 `/Applications/`。

---

## 三、`manis.spec` 是什么

`manis.spec` 是 PyInstaller 的配置文件，提交进仓库以保证构建可复现。所有打包参数都在里面：

| 关注点 | 在 spec 里的位置 |
|---|---|
| 入口文件 | `Analysis(['main.py'])` |
| 资源文件（HTML） | `datas=[('manis/web', 'manis/web')]` |
| 不打包的 GUI 库（瘦身） | `excludes=['tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx']` |
| 架构（Intel/ARM） | `target_arch='x86_64'`（M 系列 Mac 改为 `'arm64'`，通用二进制 `'universal2'`） |
| 窗口化（不弹终端） | `console=False` |
| 压缩二进制 | `strip=True`, `upx=False` |
| Bundle 元信息 | `BUNDLE(... info_plist={...})` |

修改 spec 后再跑脚本即生效，不需要改命令行参数。

---

## 四、签名与公证（分发前必做）

为避免 Gatekeeper 拦截：

```bash
# 给 .app 自签名（开发者 ID 模式需要 Apple Developer 账号）
codesign --deep --force --sign "Developer ID Application: Your Name" dist/manis.app

# 公证 (notarytool)
xcrun notarytool submit dist/manis.dmg \
    --apple-id "you@example.com" \
    --team-id "TEAMID" \
    --password "app-specific-pwd" \
    --wait
```

---

## 五、DMG 安装包

```bash
brew install create-dmg

create-dmg \
    --volname "manis" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "dist/manis.app" 175 120 \
    --hide-extension "dist/manis.app" \
    --app-drop-link 425 120 \
    "dist/manis-0.1.0.dmg" \
    "dist/manis.app"
```

---

## 六、Intel vs ARM vs Universal

| Mac | `target_arch` | 说明 |
|---|---|---|
| Intel (x86_64) | `'x86_64'` | 当前默认 |
| Apple Silicon (M1/M2/…) | `'arm64'` | 改 manis.spec 重打 |
| 通用二进制 | `'universal2'` | 需要系统同时装有 x86_64 和 arm64 两个 Python 解释器 |

判断当前 Mac：

```bash
uname -m
# x86_64  → Intel
# arm64   → Apple Silicon
```

---

## 当前文件状态

| 文件 | 状态 | 用途 |
|---|---|---|
| `manis.spec` | ✅ 提交进仓库 | PyInstaller 构建配置 |
| `scripts/build.sh` | ✅ 提交进仓库 | 一键打包 + 冒烟测试 |
| `setup.py` | ⚠️ 已弃用 | 保留作历史参考，**不要再跑** |
| `manis/app.py` | ✅ 已修改 | 自动适配打包后的资源路径 |
| `main.py` | ✅ 已修改 | 打包后的应用入口 |

---

## 七、Troubleshooting

### 启动时报 *"A Python runtime could not be located"*

打包用的 Python 不是 framework build。检查：

```bash
/usr/local/Cellar/python@3.13/3.13.11_1/bin/python3.13 \
  -c "import sysconfig; print(sysconfig.get_config_var('PYTHONFRAMEWORK'))"
# 应该输出: Python
# 如果是 None/空 → 换 brew 装的 python@3.13
```

uv 默认装的 `cpython-*-macos-x86_64-none` 后缀就是 non-framework build。

### `pyinstaller` 命令找不到 / 旧版

确认是 venv 里的版本（**不是** `~/.local/bin` 里全局那个）：

```bash
.venv/bin/pyinstaller --version
# 应该 >= 6.0
```

### .app 一启动就闪退

打开 `Console.app`，搜 `manis`，看 crash report。

最常见原因：pywebview 找不到系统 WebKit。macOS 自带，理论上不会出问题；如果你砍掉了系统依赖，可能需要装 Xcode Command Line Tools：

```bash
xcode-select --install
```
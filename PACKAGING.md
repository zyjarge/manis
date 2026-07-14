# 打包 manis 为 macOS 桌面应用

## 方案一：py2app（推荐，纯 macOS）

```bash
cd ~/workspace/manis

# 安装 py2app
uv pip install py2app

# 编译 .app
uv run python3 setup.py py2app
```

产物在 `dist/manis.app`，可以：
- 直接双击运行
- 拖到 `/Applications/` 安装
- 后续用 `hdiutil` 打包成 `.dmg`

### Intel vs ARM 架构

默认 `setup.py` 里 `arch: "x86_64"`（Intel Mac）。如果是 M1/M2 Mac 改为：
```python
"arch": "arm64"
```

通用二进制（既能 Intel 也能 ARM）：
```python
"arch": "universal2"
```
但需要系统装有两个 Python 解释器或自定义 universal Python。

## 方案二：PyInstaller（跨平台）

如果未来想打 Windows / Linux 包：

```bash
uv pip install pyinstaller
uv run pyinstaller --noconfirm --windowed \
    --name "manis" \
    --add-data "manis/web:manis/web" \
    main.py
```

产物 `dist/manis.app`（macOS）或 `dist/manis.exe`（Windows）。

## 方案三：自动签名 + 公证

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

## 方案四：DMG 安装包

```bash
# 用 create-dmg 工具
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

## 当前文件状态

- `setup.py` - py2app 配置（已创建）
- `manis/app.py` - 自动适配打包后的资源路径（已修改）
- `main.py` - 打包后的应用入口（已修改）
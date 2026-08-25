"""
py2app configuration for manis.

Build standalone .app bundle:
    uv run python3 setup.py py2app

The resulting .app will be in ./dist/manis.app
"""
import sys

if sys.platform != "darwin":
    print("Error: py2app only supports macOS")
    sys.exit(1)

# Disable pyproject.toml merging which conflicts with py2app
# Newer setuptools moved apply to ._apply_pyprojecttoml.apply
import setuptools.config.pyprojecttoml as _ppt
import setuptools.config._apply_pyprojecttoml as _ppt_apply

_original_apply = getattr(_ppt_apply, 'apply', None) or getattr(_ppt, 'apply_pyprojecttoml', None)


def _patched_apply(dist, pyprojecttoml_filename, pyproject_options):
    """Skip dynamic fields that py2app cannot handle."""
    if 'project' in pyproject_options:
        for k in ('dependencies', 'optional-dependencies', 'urls'):
            pyproject_options['project'].pop(k, None)
    if _original_apply:
        return _original_apply(dist, pyprojecttoml_filename, pyproject_options)


if _original_apply and hasattr(_ppt_apply, 'apply'):
    _ppt_apply.apply = _patched_apply
elif _original_apply:
    _ppt.apply_pyprojecttoml = _patched_apply

APP = ["main.py"]
DATA_FILES = [("web", ("manis/web/index.html",))]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": None,
    "plist": {
        "CFBundleName": "manis",
        "CFBundleDisplayName": "manis - SSH Tunnel Manager",
        "CFBundleIdentifier": "com.zhangyong.manis",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.developer-tools",
        "LSMinimumSystemVersion": "11.0",
    },
    "packages": ["manis", "webview"],
    "includes": [],
    "excludes": ["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx"],
    "site_packages": True,
    "strip": True,
    "optimize": 2,
    "arch": "x86_64",  # Intel Mac; use "arm64" for M1/M2, or "universal2" for both
}

from setuptools import setup

setup(
    app=APP,
    name="manis",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
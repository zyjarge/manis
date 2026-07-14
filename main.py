"""manis - main entry point used by py2app bundle."""

import sys


def main():
    # When running as a bundled .app, this is invoked.
    # Forward to GUI launcher.
    from manis.app import run
    run()


if __name__ == "__main__":
    main()
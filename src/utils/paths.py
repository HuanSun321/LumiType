"""Path utilities for the application."""
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Get the application data directory, creating it if needed.

    When running from PyInstaller bundle, uses %LOCALAPPDATA%/逐字拾光/.
    When running from source, uses the project root directory.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle — use AppData
        base = Path.home() / "AppData" / "Local" / "逐字拾光"
    else:
        # Running from source — use project root
        base = Path(__file__).resolve().parent.parent.parent
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_data_dir() -> Path:
    """Get the directory for built-in data files (bundled with app)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data" / "builtin"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent.parent / "data" / "builtin"


def get_builtin_data_dir() -> Path:
    """Alias for get_data_dir()."""
    return get_data_dir()

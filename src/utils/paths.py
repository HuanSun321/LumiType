import sys
from pathlib import Path

# src/utils/paths.py → src/utils → src → project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_app_dir() -> Path:
    """Get the application root directory. Works in both dev and packaged mode."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return _PROJECT_ROOT


def get_data_dir() -> Path:
    """Get the data directory (builtin JSON files)."""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
        data = base / "data" / "builtin"
        if data.exists():
            return data
        return Path(sys._MEIPASS) / "data" / "builtin"
    return _PROJECT_ROOT / "data" / "builtin"

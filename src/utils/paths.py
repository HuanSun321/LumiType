"""Path utilities for the application."""
import logging
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

LEGACY_APP_DIR = Path.home() / "AppData" / "Local" / "\u9010\u5b57\u62fe\u5149"


def _resolve_exe_dir() -> Path:
    """Return the directory containing the running executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def get_app_dir() -> Path:
    """Get the application data directory, creating it if needed.

    Frozen mode: <exe_dir>/userdata
    Source mode: project root
    """
    if getattr(sys, "frozen", False):
        base = _resolve_exe_dir() / "userdata"
    else:
        base = Path(__file__).resolve().parent.parent.parent
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_legacy_app_dir() -> Path:
    """Return the legacy AppData location used by previous versions."""
    return LEGACY_APP_DIR


def migrate_legacy_data() -> bool:
    """Copy legacy AppData files to the new userdata directory.

    Returns True if any files were migrated.
    """
    target = get_app_dir()
    legacy = LEGACY_APP_DIR
    if not legacy.exists():
        return False
    candidates = ["typehan.db", "typehan.db-wal", "typehan.db-shm", "crash.log"]
    migrated = False
    for name in candidates:
        src = legacy / name
        dst = target / name
        if not src.exists():
            continue
        if dst.exists():
            continue
        try:
            shutil.copy2(src, dst)
            migrated = True
            logger.info("Paths: migrated %s -> %s", src, dst)
        except OSError as e:
            logger.warning("Paths: failed to migrate %s: %s", src, e)
    return migrated


def get_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "data" / "builtin"
    return Path(__file__).resolve().parent.parent.parent / "data" / "builtin"


def get_builtin_data_dir() -> Path:
    return get_data_dir()


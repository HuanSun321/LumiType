import sys
import logging
from src.utils.paths import get_app_dir


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(get_app_dir() / "crash.log"), encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    try:
        from PyQt6.QtWidgets import QApplication
        from src.app import App

        app = QApplication(sys.argv)
        window = App(app)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical("Application crashed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

import sys
from src.app import App
from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("逐字拾光")
    app.setOrganizationName("逐字拾光")
    app_instance = App()
    app.aboutToQuit.connect(app_instance.db.close)

    # Set global stylesheet on QApplication so popup windows (QComboBox dropdown etc.) inherit styles
    from src.ui.theme import ThemeManager
    app.setStyleSheet(ThemeManager().get_stylesheet())

    window = MainWindow()
    # Window show is handled inside MainWindow based on config

    # Auto-update materials in background if enabled
    if app_instance.config.get("auto_update_materials"):
        from src.core.material_updater import MaterialUpdater
        from src.materials.material_manager import MaterialManager
        updater = MaterialUpdater()
        updater.finished.connect(lambda n: MaterialManager.instance().reload() if n > 0 else None)
        updater.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

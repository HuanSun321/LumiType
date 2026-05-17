from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QEvent


class InputBar(QWidget):
    """IME-aware input widget for Chinese typing.

    Emits:
      text_committed  — final character after IME candidate selection
      composing_changed — current pinyin being composed (real-time)

    In direct mode (English pinyin for falling_text), emits one character at
    a time via text_committed without waiting for IME commit.
    """
    text_committed = pyqtSignal(str)
    composing_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("✏️ 输入拼音，按空格上屏~")
        self._line_edit.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._line_edit.installEventFilter(self)
        self._line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFF8E7;
                color: #5B4A4A;
                border: 2px solid #FFD1DC;
                border-radius: 16px;
                padding: 12px 18px;
                font-size: 22px;
            }
            QLineEdit:focus {
                border-color: #FF8FAB;
                background-color: #fff8f8;
            }
        """)
        layout.addWidget(self._line_edit)

        self._is_composing = False
        self._clearing = False
        self._pending_commit = ""
        self._direct_mode = False  # True = emit every character immediately (no IME)

    def set_direct_mode(self, enabled: bool):
        """Switch to direct mode: emit every keystroke as text_committed."""
        self._direct_mode = enabled
        if enabled:
            self._line_edit.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)
            self._line_edit.setPlaceholderText("✏️ 输入拼音消除字符...")
        else:
            self._line_edit.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
            self._line_edit.setPlaceholderText("✏️ 输入拼音，按空格上屏~")

    def eventFilter(self, obj, event):
        if obj is self._line_edit and event.type() == QEvent.Type.InputMethod:
            preedit = event.preeditString()
            commit = event.commitString()

            if preedit and not commit:
                self._is_composing = True
                self.composing_changed.emit(preedit)
            elif commit:
                self._pending_commit = commit
                self._is_composing = False
                self.composing_changed.emit("")
            else:
                self._is_composing = False
                self.composing_changed.emit("")

            return False

        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str):
        if self._clearing:
            return

        # Direct mode: emit each character immediately, no IME logic
        if self._direct_mode:
            if not text:
                return
            self.text_committed.emit(text)
            self._clearing = True
            self._line_edit.clear()
            self._clearing = False
            return

        if self._is_composing:
            return

        if not text:
            self._pending_commit = ""
            self.composing_changed.emit("")
            return

        committed = self._pending_commit if self._pending_commit else text
        self._pending_commit = ""
        self.composing_changed.emit("")
        self.text_committed.emit(committed)

        self._clearing = True
        self._line_edit.clear()
        self._clearing = False

    def setFocus(self):
        self._line_edit.setFocus()

    def setEnabled(self, enabled: bool):
        self._line_edit.setEnabled(enabled)

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from unidecode import unidecode


class PlainTextPasteTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        # Check for Ctrl+V (Paste shortcut)
        if event.key() == Qt.Key_V and (event.modifiers() & Qt.ControlModifier):
            self.handle_paste()
        else:
            # Handle regular key press
            text = event.text()
            if text:
                utf8_text = unidecode(text)
                # Insert the converted text manually
                cursor = self.textCursor()
                cursor.insertText(utf8_text)
            else:
                # Call parent method if no text to process (e.g., for non-character keys)
                super().keyPressEvent(event)

    def handle_paste(self):
        # Get the text from the clipboard
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        # Convert the clipboard text to UTF-8 using unidecode
        utf8_text = unidecode(text)

        # Insert the converted text into the editor
        self.insertPlainText(utf8_text)

    def event(self, event):
        # Intercept the clipboard paste event
        if event.type() == QEvent.Clipboard:
            self.handle_paste()
            return True
        return super().event(event)

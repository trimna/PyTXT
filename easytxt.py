import os
import sys
import ctypes
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5 import uic


def resource_path(filename):

    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)

        paths = [
            os.path.join(base_dir, filename),
            os.path.join(base_dir, "_internal", filename)
        ]

    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

        paths = [
            os.path.join(base_dir, filename)
        ]

    for path in paths:
        if os.path.isfile(path):
            return path

    raise FileNotFoundError(
        f"Arquivo não encontrado: {filename}\n\n"
        f"Caminhos procurados:\n" +
        "\n".join(paths)
    )


class FontDialog(QDialog):

    def __init__(self, current_font, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Edit Font Info")

        layout = QVBoxLayout(self)

        font_label = QLabel("Font:")

        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(current_font)

        size_label = QLabel("Size:")

        self.size_box = QSpinBox()
        self.size_box.setRange(1, 100)
        self.size_box.setValue(current_font.pointSize())

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok |
            QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(font_label)
        layout.addWidget(self.font_box)
        layout.addWidget(size_label)
        layout.addWidget(self.size_box)
        layout.addWidget(buttons)

    def get_font(self):
        font = QFont(self.font_box.currentFont())
        font.setPointSize(self.size_box.value())
        return font


class TheGUI(QMainWindow):

    def __init__(self):
        super(TheGUI, self).__init__()

        try:
            ui_path = resource_path("untitled.ui")
            uic.loadUi(ui_path, self)
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error starting up",
                f"Unable to load the PyTXT interface.:\n\n{e}"
            )
            sys.exit(1)

        self.setWindowTitle("PyTXT")

        try:
            icon_path = resource_path("PyTXT.ico")
            if os.path.isfile(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self.actionOpen.triggered.connect(
            self.open_file
        )

        self.actionSave.triggered.connect(
            self.save_file
        )

        self.actionExit.triggered.connect(
            self.close
        )

        self.actionUndo.triggered.connect(
            self.textEdit.undo
        )

        self.actionRedo.triggered.connect(
            self.textEdit.redo
        )

        self.actionCopy.triggered.connect(
            self.textEdit.copy
        )

        self.actionSelect_All.triggered.connect(
            self.textEdit.selectAll
        )

        self.actionLight_Mode.triggered.connect(
            self.light_mode
        )

        self.actionDark_Mode.triggered.connect(
            self.dark_mode
        )

        self.actionEdit_Font_Info.triggered.connect(
            self.edit_font
        )

        self.current_file = None
        self.textEdit.textChanged.connect(self._mark_modified)
        self._modified = False

        self.show()

    def open_path(self, filename):
        """Opens a specific file (used when receiving the path
        via the command line, when PyTXT is the default
        Explorer app for .txt files)."""

        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error while opening file",
                f"Could not open the file:\n{filename}\n\n{e}"
            )
            return

        self.textEdit.setText(content)
        self.current_file = filename
        self._modified = False

    def _mark_modified(self):
        self._modified = True

    def _confirm_discard_changes(self):
        """Asks the user if they want to discard unsaved changes.
        Returns True if it can proceed (open another file / close)."""

        if not self._modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved changes",
            "There are unsaved changes. Do you want to save before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if reply == QMessageBox.Save:
            return self.save_file()
        elif reply == QMessageBox.Discard:
            return True
        else:
            return False

    def open_file(self):

        if not self._confirm_discard_changes():
            return

        options = QFileDialog.Options()

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "r",
                encoding="utf-8"
            ) as f:
                content = f.read()

        except UnicodeDecodeError:
            QMessageBox.critical(
                self,
                "Error opening file",
                "The file is not in UTF-8 and could not be read."
                "Try opening a valid text file."
            )
            return

        except PermissionError:
            QMessageBox.critical(
                self,
                "Error opening file",
                "You have no permission to read this file."
            )
            return

        except OSError as e:
            QMessageBox.critical(
                self,
                "Error opening file",
                f"Could not open the file:\n{e}"
            )
            return

        self.textEdit.setText(content)
        self.current_file = filename
        self._modified = False

    def save_file(self):

        options = QFileDialog.Options()

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            self.current_file or "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )

        if not filename:
            return False

        try:
            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(
                    self.textEdit.toPlainText()
                )

        except PermissionError:
            QMessageBox.critical(
                self,
                "Error while saving",
                "You do not have permission to save this file in this location."
            )
            return False

        except OSError as e:
            QMessageBox.critical(
                self,
                "Error while saving",
                f"Could not save the file:\n{e}"
            )
            return False

        self.current_file = filename
        self._modified = False
        return True

    def light_mode(self):

        self.setStyleSheet("")

    def dark_mode(self):

        self.setStyleSheet("""
            QMainWindow {
                background-color: #202020;
            }

            QTextEdit {
                background-color: #181818;
                color: #eeeeee;
                border: 1px solid #444444;
                selection-background-color: #555555;
            }

            QMenuBar {
                background-color: #202020;
                color: #eeeeee;
            }

            QMenuBar::item:selected {
                background-color: #404040;
            }

            QMenu {
                background-color: #202020;
                color: #eeeeee;
            }

            QMenu::item:selected {
                background-color: #404040;
            }

            QStatusBar {
                background-color: #202020;
                color: #eeeeee;
            }
        """)

    def edit_font(self):

        dialog = FontDialog(
            self.textEdit.font(),
            self
        )

        if dialog.exec_() == QDialog.Accepted:

            self.textEdit.setFont(
                dialog.get_font()
            )

    def closeEvent(self, event):
        """Prevents the loss of unsaved text when closing the window."""
        if self._confirm_discard_changes():
            event.accept()
        else:
            event.ignore()


def main():

    try:
        myappid = "trimnalosite.pytxt.editor.1.1"

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            myappid
        )

    except Exception:
        pass

    app = QApplication(sys.argv)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        print(error_msg, file=sys.stderr)

        QMessageBox.critical(
            None,
            "Unexpected error",
            f"An unexpected error occurred:\n\n{exc_value}"
        )

    sys.excepthook = handle_exception

    try:
        window = TheGUI()
    except Exception as e:
        QMessageBox.critical(None, "Error starting up", str(e))
        sys.exit(1)


    if len(sys.argv) > 1:
        window.open_path(sys.argv[1])

    sys.exit(
        app.exec_()
    )


if __name__ == "__main__":
    main()

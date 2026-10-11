import os, sys, ctypes, traceback

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTextEdit, QMenuBar, QMenu,
    QStatusBar, QAction, QMessageBox, QFileDialog, QDialog,
    QVBoxLayout, QLabel, QFontComboBox, QSpinBox,
    QDialogButtonBox, QTabWidget, QPushButton
)

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QTimer


def resource_path(filename):
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        paths = [
            os.path.join(base_dir, filename),
            os.path.join(base_dir, "_internal", filename)
        ]
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        paths = [os.path.join(base_dir, filename)]

    for path in paths:
        if os.path.isfile(path):
            return path

    raise FileNotFoundError(f"Could not find resource file: {filename}")


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
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
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


class GoToLineDialog(QDialog):
    def __init__(self, max_lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Go to Line")
        self.resize(250, 90)

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Line number (1 - {max_lines}):")
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, max_lines)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self.label)
        layout.addWidget(self.spin_box)
        layout.addWidget(buttons)

    def get_line(self):
        return self.spin_box.value()


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_tab_button = None

    def set_new_tab_button(self, button):
        self.new_tab_button = button
        button.setParent(self)
        button.raise_()
        self.position_new_tab_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_new_tab_button()

    def position_new_tab_button(self):
        if self.new_tab_button:
            button = self.new_tab_button
            x = self.width() - button.width() - 4
            y = 2
            button.move(x, y)
            button.raise_()


class TheGUI(QMainWindow):
    instances = []

    def __init__(self, file_to_open=None):
        super().__init__()
        TheGUI.instances.append(self)

        try:
            self.init_ui()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Error starting up",
                f"Unable to load the PyTXT interface:\n\n{e}"
            )
            sys.exit(1)

        self.setWindowTitle("PyTXT")

        try:
            icon_path = resource_path("PyTXT.ico")
            if os.path.isfile(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self.actionNewTab.triggered.connect(lambda: self.new_tab())
        self.actionNewWindow.triggered.connect(self.new_window)
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_file)
        self.actionExit.triggered.connect(self.close)

        self.actionUndo.triggered.connect(self.current_undo)
        self.actionRedo.triggered.connect(self.current_redo)
        self.actionCut.triggered.connect(self.current_cut)
        self.actionCopy.triggered.connect(self.current_copy)
        self.actionPaste.triggered.connect(self.current_paste)
        self.actionSelect_All.triggered.connect(self.current_select_all)
        self.actionGoToLine.triggered.connect(self.open_go_to_line)

        self.actionLight_Mode.triggered.connect(self.light_mode)
        self.actionDark_Mode.triggered.connect(self.dark_mode)
        self.actionEdit_Font_Info.triggered.connect(self.edit_font)

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(30000)
        self.auto_save_timer.timeout.connect(self.perform_auto_save)
        self.auto_save_timer.start()

        if file_to_open:
            self.open_path(file_to_open)
        else:
            self.new_tab("Untitled.txt")

        self.show()

    def init_ui(self):
        self.setObjectName("MainWindow")
        self.resize(800, 600)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        central_layout = QVBoxLayout(self.centralwidget)
        central_layout.setContentsMargins(5, 5, 5, 5)

        self.tab_widget = TabWidget(self.centralwidget)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab_at)
        self.tab_widget.currentChanged.connect(self.tab_changed)

        self.new_tab_btn = QPushButton("+", self.tab_widget)
        self.new_tab_btn.setFixedSize(28, 24)
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.clicked.connect(lambda: self.new_tab())

        self.tab_widget.set_new_tab_button(self.new_tab_btn)

        central_layout.addWidget(self.tab_widget)
        self.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(self)
        self.menubar.setObjectName("menubar")

        self.menuFile = QMenu("File", self.menubar)
        self.menuEdit = QMenu("Edit", self.menubar)
        self.menuOptions = QMenu("Options", self.menubar)
        self.menuTheme = QMenu("Theme", self.menuOptions)

        self.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.char_word_label = QLabel("Words: 0 | Characters: 0")
        self.statusbar.addPermanentWidget(self.char_word_label)

        self.actionNewTab = QAction("New Tab", self)
        self.actionNewTab.setShortcut("Ctrl+T")

        self.actionNewWindow = QAction("New Window", self)
        self.actionNewWindow.setShortcut("Ctrl+Shift+N")

        self.actionOpen = QAction("Open", self)
        self.actionOpen.setShortcut("Ctrl+O")

        self.actionSave = QAction("Save", self)
        self.actionSave.setShortcut("Ctrl+S")

        self.actionExit = QAction("Exit", self)
        self.actionExit.setShortcut("Ctrl+Q")

        self.actionUndo = QAction("Undo", self)
        self.actionUndo.setShortcut("Ctrl+Z")

        self.actionRedo = QAction("Redo", self)
        self.actionRedo.setShortcut("Ctrl+Y")

        self.actionCut = QAction("Cut", self)
        self.actionCut.setShortcut("Ctrl+X")

        self.actionCopy = QAction("Copy", self)
        self.actionCopy.setShortcut("Ctrl+C")

        self.actionPaste = QAction("Paste", self)
        self.actionPaste.setShortcut("Ctrl+V")

        self.actionSelect_All = QAction("Select All", self)
        self.actionSelect_All.setShortcut("Ctrl+A")

        self.actionGoToLine = QAction("Go to Line...", self)
        self.actionGoToLine.setShortcut("Ctrl+G")

        self.actionLight_Mode = QAction("Light Mode", self)
        self.actionDark_Mode = QAction("Dark Mode", self)
        self.actionEdit_Font_Info = QAction("Edit Font Info", self)

        self.menuFile.addAction(self.actionNewTab)
        self.menuFile.addAction(self.actionNewWindow)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionGoToLine)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelect_All)

        self.menuTheme.addAction(self.actionLight_Mode)
        self.menuTheme.addAction(self.actionDark_Mode)

        self.menuOptions.addMenu(self.menuTheme)
        self.menuOptions.addAction(self.actionEdit_Font_Info)

        self.menubar.addMenu(self.menuFile)
        self.menubar.addMenu(self.menuEdit)
        self.menubar.addMenu(self.menuOptions)

    def current_editor(self):
        widget = self.tab_widget.currentWidget()

        if widget:
            return widget.findChild(QTextEdit)

        return None

    def new_window(self):
        new_win = TheGUI()
        new_win.show()

    def new_tab(self, title="Untitled.txt", content=""):
        tab_page = QWidget()
        layout = QVBoxLayout(tab_page)
        layout.setContentsMargins(0, 0, 0, 0)

        editor = QTextEdit(tab_page)
        editor.setText(content)

        layout.addWidget(editor)

        tab_page.current_file = None
        tab_page._modified = False

        editor.textChanged.connect(
            lambda: self.mark_modified(tab_page)
        )
        editor.textChanged.connect(self.update_statusbar)

        self.tab_widget.addTab(tab_page, title)
        self.tab_widget.setCurrentWidget(tab_page)
        self.update_statusbar()

        return tab_page

    def mark_modified(self, tab_page):
        tab_page._modified = True

        index = self.tab_widget.indexOf(tab_page)
        current_text = self.tab_widget.tabText(index)

        if not current_text.endswith("*"):
            self.tab_widget.setTabText(index, current_text + "*")

    def unmark_modified(self, tab_page, filename):
        tab_page._modified = False

        index = self.tab_widget.indexOf(tab_page)
        base_name = os.path.basename(filename)

        self.tab_widget.setTabText(index, base_name)

    def update_statusbar(self):
        editor = self.current_editor()

        if editor:
            text = editor.toPlainText()
            chars = len(text)
            words = len(text.split()) if text.strip() else 0
            self.char_word_label.setText(
                f"Words: {words} | Characters: {chars}"
            )
        else:
            self.char_word_label.setText(
                "Words: 0 | Characters: 0"
            )

    def tab_changed(self, index):
        self.update_statusbar()

    def confirm_discard_changes(self, tab_page):
        if not tab_page._modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved changes",
            f"The document '{self.tab_widget.tabText(self.tab_widget.indexOf(tab_page))}' has unsaved changes. Save before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if reply == QMessageBox.Save:
            return self.save_file_for_tab(tab_page)

        elif reply == QMessageBox.Discard:
            return True

        return False

    def close_tab_at(self, index):
        tab_page = self.tab_widget.widget(index)

        if self.confirm_discard_changes(tab_page):
            self.tab_widget.removeTab(index)

            if self.tab_widget.count() == 0:
                self.new_tab("Untitled.txt")

    def open_path(self, filename):
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

        current_page = self.tab_widget.currentWidget()
        editor = self.current_editor()

        if (
            current_page
            and not current_page._modified
            and editor
            and not editor.toPlainText().strip()
            and not current_page.current_file
        ):
            editor.setText(content)
            current_page.current_file = filename
            self.unmark_modified(current_page, filename)

        else:
            page = self.new_tab(os.path.basename(filename), content)
            page.current_file = filename
            self.unmark_modified(page, filename)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if not filename:
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()

        except UnicodeDecodeError:
            QMessageBox.critical(
                self,
                "Error opening file",
                "The file is not in UTF-8 and could not be read."
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

        self.open_path(filename)

    def save_file(self):
        tab_page = self.tab_widget.currentWidget()

        if not tab_page:
            return False

        return self.save_file_for_tab(tab_page)

    def save_file_for_tab(self, tab_page):
        editor = tab_page.findChild(QTextEdit)

        if not editor:
            return False

        filename = tab_page.current_file

        if not filename:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                "",
                "Text Files (*.txt);;All Files (*)"
            )

            if not filename:
                return False

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())

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

        tab_page.current_file = filename
        self.unmark_modified(tab_page, filename)

        return True

    def perform_auto_save(self):
        for i in range(self.tab_widget.count()):
            tab_page = self.tab_widget.widget(i)

            if (
                tab_page
                and tab_page._modified
                and tab_page.current_file
            ):
                editor = tab_page.findChild(QTextEdit)

                if editor:
                    try:
                        with open(
                            tab_page.current_file,
                            "w",
                            encoding="utf-8"
                        ) as f:
                            f.write(editor.toPlainText())

                        self.unmark_modified(
                            tab_page,
                            tab_page.current_file
                        )

                        self.statusbar.showMessage(
                            f"Auto-saved: {os.path.basename(tab_page.current_file)}",
                            3000
                        )

                    except Exception:
                        pass

    def current_undo(self):
        ed = self.current_editor()

        if ed:
            ed.undo()

    def current_redo(self):
        ed = self.current_editor()

        if ed:
            ed.redo()

    def current_cut(self):
        ed = self.current_editor()

        if ed:
            ed.cut()

    def current_copy(self):
        ed = self.current_editor()

        if ed:
            cursor = ed.textCursor()

            if cursor.hasSelection():
                clipboard = QApplication.clipboard()
                clipboard.setText(cursor.selectedText())

    def current_paste(self):
        ed = self.current_editor()

        if ed:
            ed.paste()

    def current_select_all(self):
        ed = self.current_editor()

        if ed:
            ed.selectAll()

    def open_go_to_line(self):
        ed = self.current_editor()

        if not ed:
            return

        doc = ed.document()
        max_lines = doc.lineCount()

        dialog = GoToLineDialog(max_lines, self)

        if dialog.exec_() == QDialog.Accepted:
            target_line = dialog.get_line()
            block = doc.findBlockByLineNumber(target_line - 1)

            if block.isValid():
                cursor = ed.textCursor()
                cursor.setPosition(block.position())
                ed.setTextCursor(cursor)

    def light_mode(self):
        self.setStyleSheet("")
        self.new_tab_btn.setStyleSheet("")

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

            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #181818;
            }

            QTabBar::tab {
                background-color: #2d2d2d;
                color: #aaaaaa;
                padding: 6px 12px;
                border: 1px solid #444444;
                border-bottom: none;
            }

            QTabBar::tab:selected {
                background-color: #181818;
                color: #eeeeee;
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

        self.new_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #eeeeee;
                border: 1px solid #444444;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #404040;
            }
        """)

        self.tab_widget.position_new_tab_button()

    def edit_font(self):
        editor = self.current_editor()

        if not editor:
            return

        dialog = FontDialog(editor.font(), self)

        if dialog.exec_() == QDialog.Accepted:
            new_font = dialog.get_font()
            editor.setFont(new_font)

    def closeEvent(self, event):
        for i in range(self.tab_widget.count()):
            tab_page = self.tab_widget.widget(i)

            if not self.confirm_discard_changes(tab_page):
                event.ignore()
                return

        try:
            TheGUI.instances.remove(self)
        except ValueError:
            pass

        event.accept()


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
            sys.__excepthook__(
                exc_type,
                exc_value,
                exc_traceback
            )
            return

        error_msg = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback
            )
        )

        print(error_msg, file=sys.stderr)

        QMessageBox.critical(
            None,
            "Unexpected error",
            f"An unexpected error occurred:\n\n{exc_value}"
        )

    sys.excepthook = handle_exception

    try:
        initial_file = sys.argv[1] if len(sys.argv) > 1 else None
        window = TheGUI(initial_file)
    except Exception as e:
        QMessageBox.critical(
            None,
            "Error starting up",
            str(e)
        )
        sys.exit(1)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

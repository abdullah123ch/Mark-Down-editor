import os
import markdown
import pdfkit
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, QSplitter,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QMessageBox,
    QListWidget, QListWidgetItem, QTabWidget, QAction, QMenu, QStyleFactory
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MarkdownTab(QWidget):
    def __init__(self, filepath=None):
        super().__init__()
        self.filepath = filepath

        layout = QHBoxLayout(self)
        self.text_edit = QTextEdit()
        self.preview = QWebEngineView()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.preview)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

        self.text_edit.textChanged.connect(self.update_preview)
        self.update_preview()

    def update_preview(self):
        md_text = self.text_edit.toPlainText()
        html = markdown.markdown(md_text, extensions=["fenced_code", "codehilite"])
        css = self.load_css()

        full_html = f"""
        <html><head><meta charset='utf-8'><style>{css}</style></head>
        <body>{html}</body></html>
        """
        self.preview.setHtml(full_html)

    def load_css(self):
        path = "theme/preview_dark.css" if QApplication.instance().property("theme") == "dark" else "theme/preview.css"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return "body { font-family: sans-serif; font-size: 14px; padding: 20px; }"

class MarkdownEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor")
        self.setGeometry(100, 100, 1000, 600)

        self.current_dir = os.getcwd()
        self.recent_files = []
        self.theme = "light"

        self.sidebar = QListWidget()
        self.sidebar.itemClicked.connect(self.open_file_from_sidebar)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        main_split = QSplitter(Qt.Horizontal)
        main_split.addWidget(self.sidebar)
        main_split.addWidget(self.tabs)
        main_split.setSizes([200, 800])

        main_layout = QVBoxLayout()
        toolbar = QHBoxLayout()

        # Toolbar icons
        self.add_toolbar_icon(toolbar, "icons/new.png", self.new_tab, "New File")
        self.add_toolbar_icon(toolbar, "icons/open.png", self.open_file, "Open File")
        self.add_toolbar_icon(toolbar, "icons/save.png", self.save_file, "Save File")
        self.add_toolbar_icon(toolbar, "icons/pdf.png", self.export_pdf, "Export as PDF")
        self.add_toolbar_icon(toolbar, "icons/theme.png", self.toggle_theme, "Toggle Theme")

        # Formatting buttons
        self.add_toolbar_icon(toolbar, "icons/bold.png", lambda: self.insert_md("**", "**"), "Bold (**text**)")
        self.add_toolbar_icon(toolbar, "icons/italic.png", lambda: self.insert_md("*", "*"), "Italic (*text*)")
        self.add_toolbar_icon(toolbar, "icons/heading.png", lambda: self.insert_md("# ", ""), "Heading (# Heading)")
        self.add_toolbar_icon(toolbar, "icons/subheading.png", lambda: self.insert_md("## ", ""), "Subheading (## Heading)")

        container = QWidget()
        container.setLayout(main_layout)
        main_layout.addLayout(toolbar)
        main_layout.addWidget(main_split)
        self.setCentralWidget(container)

        self.init_menu()
        self.populate_sidebar()
        QApplication.instance().setProperty("theme", "light")

    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = QAction("Open File...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        self.recent_menu = QMenu("Open Recent", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.clear()
        for path in self.recent_files[-5:]:
            action = QAction(os.path.basename(path), self)
            action.triggered.connect(lambda _, p=path: self.load_tab_from_file(p))
            self.recent_menu.addAction(action)

    def add_recent_file(self, path):
        if path not in self.recent_files:
            self.recent_files.append(path)
        self.update_recent_menu()

    def add_toolbar_icon(self, layout, icon_path, func, tooltip):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setToolTip(tooltip)
        btn.clicked.connect(func)
        layout.addWidget(btn)

    def insert_md(self, prefix, suffix=""):
        tab = self.current_tab()
        if not tab:
            return
        cursor = tab.text_edit.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
        tab.update_preview()

    def current_tab(self):
        return self.tabs.currentWidget()

    def new_tab(self):
        tab = MarkdownTab()
        self.tabs.addTab(tab, "Untitled")
        self.tabs.setCurrentWidget(tab)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Markdown", "", "Markdown Files (*.md)")
        if path:
            self.load_tab_from_file(path)

    def open_file_from_sidebar(self, item):
        path = item.data(Qt.UserRole)
        self.load_tab_from_file(path)

    def load_tab_from_file(self, path):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if getattr(tab, 'filepath', None) == path:
                self.tabs.setCurrentIndex(i)
                return

        tab = MarkdownTab(filepath=path)
        with open(path, "r", encoding="utf-8") as f:
            tab.text_edit.setText(f.read())
        tab.update_preview()
        self.tabs.addTab(tab, os.path.basename(path))
        self.tabs.setCurrentWidget(tab)
        self.add_recent_file(path)

    def save_file(self):
        tab = self.current_tab()
        if not tab:
            return
        path = tab.filepath
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Markdown Files (*.md)")
            if not path:
                return
            tab.filepath = path
        with open(path, "w", encoding="utf-8") as f:
            f.write(tab.text_edit.toPlainText())
        self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
        self.add_recent_file(path)
        QMessageBox.information(self, "Saved", f"Saved to {path}")

    def export_pdf(self):
        tab = self.current_tab()
        if not tab:
            return
        html = markdown.markdown(tab.text_edit.toPlainText(), extensions=["fenced_code", "codehilite"])
        css = tab.load_css()
        full_html = f"<html><head><style>{css}</style></head><body>{html}</body></html>"

        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            pdfkit.from_string(full_html, path)
            QMessageBox.information(self, "Exported", f"PDF saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    def toggle_theme(self):
        if self.theme == "light":
            self.theme = "dark"
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            QApplication.instance().setProperty("theme", "dark")
        else:
            self.theme = "light"
            QApplication.setStyle(QStyleFactory.create("Fusion"))
            QApplication.instance().setProperty("theme", "light")
        for i in range(self.tabs.count()):
            self.tabs.widget(i).update_preview()

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def populate_sidebar(self, directory="."):
        self.sidebar.clear()
        for file in os.listdir(directory):
            if file.endswith(".md"):
                item = QListWidgetItem(file)
                item.setData(Qt.UserRole, os.path.abspath(file))
                self.sidebar.addItem(item)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MarkdownEditor()
    window.show()
    sys.exit(app.exec_())

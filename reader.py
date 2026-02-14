#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Reader
Version: 0.0.3 - Fix: Hex Colors
"""

import sys
import re
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextBrowser, QListWidget, QListWidgetItem,
                             QFileDialog, QDialog, QCalendarWidget, QDialogButtonBox)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QIcon
from PyQt5.QtCore import Qt

class EntryViewerWindow(QMainWindow):
    def __init__(self, day_file, settings, parent=None):
        super().__init__(parent)
        self.day_file = Path(day_file)
        self.text_browser = QTextBrowser()
        self.setCentralWidget(self.text_browser)
        self.load_entry()

    def load_entry(self):
        if self.day_file.exists():
            with open(self.day_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.display_content(content)

    def display_content(self, content):
        self.text_browser.clear()
        cursor = self.text_browser.textCursor()
        for line in content.split('\n'):
            match = re.match(r'\{(\d+)\|([FfKkUuDd]{4})\|([^}]+)\}', line)
            if match:
                size, style, color = int(match.group(1)), match.group(2), match.group(3)
                self.insert_formatted_line(cursor, line[match.end():], (size, style, color))
            else:
                cursor.insertText(line + '\n')

    def insert_formatted_line(self, cursor, line, format_info):
        size, style, color = format_info
        fmt = QTextCharFormat()
        f = QFont()
        f.setPointSize(size)
        f.setBold('F' in style)
        f.setItalic('K' in style)
        fmt.setFont(f)
        
        # Farbauswahl: Hex-Code oder Name
        if color.startswith('#'):
            fmt.setForeground(QColor(color))
        else:
            cmap = {"Schwarz": "#000000", "Rot": "#ff0000", "Grün": "#008000", "Blau": "#0000ff"}
            fmt.setForeground(QColor(cmap.get(color, "#000000")))
            
        cursor.insertText(line + '\n', fmt)

class DiaryReader(QMainWindow):
    def __init__(self, config_file):
        super().__init__()
        self.setWindowTitle("Tagesgans Reader")
        self.setMinimumSize(400, 600)
        btn = QPushButton("Eintrag öffnen")
        btn.clicked.connect(self.open_file)
        self.setCentralWidget(btn)

    def open_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Tag wählen", filter="Day.txt")
        if f:
            self.win = EntryViewerWindow(f, {})
            self.win.show()

def main():
    app = QApplication(sys.argv)
    reader = DiaryReader(sys.argv[1] if len(sys.argv) > 1 else "config.json")
    reader.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

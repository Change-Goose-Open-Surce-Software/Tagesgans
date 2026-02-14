#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Editor - DuckDiary
Version: 0.0.3 - Fix: Indentation & Crash
"""

import sys
import os
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QToolBar, QAction, QFileDialog,
                             QColorDialog, QSpinBox, QComboBox, QDialog, QFormLayout,
                             QDialogButtonBox, QListWidget, QListWidgetItem, QMessageBox,
                             QCalendarWidget, QLineEdit, QInputDialog, QPlainTextEdit)
from PyQt5.QtCore import Qt, QUrl, QDate, QMimeData
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QIcon, QTextCursor


class DatePickerDialog(QDialog):
    """Dialog zur Datumsauswahl - Absturzsicher"""
    
    def __init__(self, parent=None, language="Deutsch"):
        super().__init__(parent)
        self.language = language
        self.selected_date = datetime.now()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Datum wählen" if self.language == "Deutsch" else "Select Date")
        layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        # Die problematische Zeile wurde entfernt, um Abstürze zu verhindern
        self.calendar.setNavigationBarVisible(True)
        
        layout.addWidget(self.calendar)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def get_date(self):
        qdate = self.calendar.selectedDate()
        return datetime(qdate.year(), qdate.month(), qdate.day())

class CreateDiaryDialog(QDialog):
    """Dialog zum Erstellen eines neuen Tagebuchs"""
    def __init__(self, parent=None, language="Deutsch"):
        super().__init__(parent)
        self.language = language
        self.icon_path = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Neues Tagebuch erstellen" if self.language == "Deutsch" else "Create New Diary")
        layout = QFormLayout()
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        self.path_edit = QLineEdit(str(Path.home()))
        layout.addRow("Pfad:", self.path_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_diary_info(self):
        return {"name": self.name_edit.text(), "path": Path(self.path_edit.text()), "icon": None}

class DiaryEditor(QMainWindow):
    """Hauptfenster des Tagebuch-Editors"""
    
    def __init__(self, config_file, mode="edit"):
        super().__init__()
        self.config_file = Path(config_file)
        self.settings = self.load_settings()
        self.mode = mode
        self.current_diary = None
        self.current_entry = None
        self.current_date = datetime.now()
        self.vcards = {}
        self.kmls = {}
        self.media_files = []
        
        self.init_ui()
        if mode == "create":
            self.create_new_diary()
        else:
            self.scan_diaries()
    
    def load_settings(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"language": "Deutsch", "default_format": "{20|fkud|#000000}"}

    def init_ui(self):
        lang = self.settings.get("language", "Deutsch")
        self.setWindowTitle("Tagesgans Editor")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        if self.mode == "edit":
            self.diary_combo = QComboBox()
            self.diary_combo.currentIndexChanged.connect(self.on_diary_selected)
            main_layout.addWidget(self.diary_combo)
            
            self.entry_list = QListWidget()
            self.entry_list.itemClicked.connect(self.on_entry_selected)
            main_layout.addWidget(self.entry_list)
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Monospace", 12))
        main_layout.addWidget(self.text_edit)
        
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_entry)
        main_layout.addWidget(save_btn)
        
        self.create_toolbar()
        central_widget.setLayout(main_layout)

    def create_toolbar(self):
        toolbar = self.addToolBar("Format")
        
        format_btn = QPushButton("Format")
        format_btn.clicked.connect(self.insert_format)
        toolbar.addWidget(format_btn)
        
        media_btn = QPushButton("+ Medien")
        media_btn.clicked.connect(self.insert_media)
        toolbar.addWidget(media_btn)

    def insert_format(self):
        """Öffnet den Farbdialog und fügt das Format-Tag ein"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Format einfügen")
        layout = QFormLayout()
        
        size_spin = QSpinBox()
        size_spin.setRange(8, 72)
        size_spin.setValue(20)
        layout.addRow("Größe:", size_spin)
        
        style_layout = QVBoxLayout()
        fett = QCheckBox("Fett (F)")
        kursiv = QCheckBox("Kursiv (K)")
        unter = QCheckBox("Unterstrichen (U)")
        durch = QCheckBox("Durchgestrichen (D)")
        for w in [fett, kursiv, unter, durch]: style_layout.addWidget(w)
        layout.addRow("Stil:", style_layout)
        
        self.selected_color = "#000000"
        color_btn = QPushButton("Farbe wählen...")
        def choose():
            c = QColorDialog.getColor()
            if c.isValid():
                self.selected_color = c.name()
                color_btn.setStyleSheet(f"background-color: {self.selected_color};")
        color_btn.clicked.connect(choose)
        layout.addRow("Farbe:", color_btn)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dialog.accept)
        bb.rejected.connect(dialog.reject)
        layout.addWidget(bb)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            s = "".join(["F" if fett.isChecked() else "f", "K" if kursiv.isChecked() else "k",
                         "U" if unter.isChecked() else "u", "D" if durch.isChecked() else "d"])
            self.text_edit.insertPlainText(f"{{{size_spin.value()}|{s}|{self.selected_color}}}")

    def insert_media(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Medien wählen")
        if file_path:
            self.media_files.append(file_path)
            self.text_edit.insertPlainText(f"[[{Path(file_path).name}]]")

    def save_entry(self):
        if not self.current_diary: return
        day_dir = self.current_diary / str(self.current_date.year) / self.current_date.strftime("%B") / f"{self.current_date.day:02d}"
        day_dir.mkdir(parents=True, exist_ok=True)
        with open(day_dir / "Day.txt", 'w', encoding='utf-8') as f:
            f.write(self.text_edit.toPlainText())
        for m in self.media_files: shutil.copy(m, day_dir / Path(m).name)
        QMessageBox.information(self, "Erfolg", "Gespeichert!")

    def scan_diaries(self):
        self.diary_combo.clear()
        base_path = Path.home() / "Documents" / "Tagebücher"
        if base_path.exists():
            for d in base_path.glob("*.duckday"):
                self.diary_combo.addItem(d.name, d)

    def on_diary_selected(self, index):
        self.current_diary = self.diary_combo.itemData(index)
        self.load_entries()

    def load_entries(self):
        self.entry_list.clear()
        # Hier würde die Logik zum Auflisten der Tage folgen...

    def create_new_diary(self):
        dialog = CreateDiaryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            info = dialog.get_diary_info()
            path = info["path"] / f"{info['name']}.duckday"
            path.mkdir(parents=True, exist_ok=True)
            self.scan_diaries()

def main():
    app = QApplication(sys.argv)
    editor = DiaryEditor(sys.argv[1] if len(sys.argv) > 1 else "config.json")
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

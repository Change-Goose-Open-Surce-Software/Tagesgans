#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Editor - DuckDiary
Creates and edits diary entries
Version: 0.0.1
"""

import sys
import os
import json
import re
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QToolBar, QAction, QFileDialog,
                             QColorDialog, QSpinBox, QComboBox, QDialog, QFormLayout,
                             QDialogButtonBox, QListWidget, QListWidgetItem, QMessageBox,
                             QCalendarWidget, QLineEdit, QInputDialog)
from PyQt5.QtCore import Qt, QUrl, QDate, QMimeData
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QIcon, QTextCursor


class DatePickerDialog(QDialog):
    """Dialog zur Datumsauswahl"""
    
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
        layout.addWidget(self.calendar)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_date(self):
        """Gibt das ausgewählte Datum zurück"""
        qdate = self.calendar.selectedDate()
        return datetime(qdate.year(), qdate.month(), qdate.day())


class CreateDiaryDialog(QDialog):
    """Dialog zum Erstellen eines neuen Tagebuchs"""
    
    def __init__(self, parent=None, language="Deutsch"):
        super().__init__(parent)
        self.language = language
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Neues Tagebuch erstellen" if self.language == "Deutsch" else "Create New Diary")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        layout.addRow("Name:" if self.language == "English" else "Name:", self.name_edit)
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(str(Path.home()))
        browse_btn = QPushButton("..." if self.language == "English" else "...")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        
        layout.addRow("Speicherort:" if self.language == "Deutsch" else "Location:", path_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def browse_path(self):
        """Pfad auswählen"""
        path = QFileDialog.getExistingDirectory(self, "Ordner auswählen", str(Path.home()))
        if path:
            self.path_edit.setText(path)
    
    def get_diary_info(self):
        """Gibt Tagebuch-Informationen zurück"""
        return {
            "name": self.name_edit.text(),
            "path": Path(self.path_edit.text())
        }


class DiaryEditor(QMainWindow):
    """Hauptfenster des Tagebuch-Editors"""
    
    def __init__(self, config_file, mode="edit"):
        super().__init__()
        self.config_file = Path(config_file)
        self.settings = self.load_settings()
        self.mode = mode  # "edit" oder "create"
        self.current_diary = None
        self.current_entry = None
        self.current_date = None
        
        self.init_ui()
        
        if mode == "create":
            self.create_new_diary()
        else:
            self.scan_diaries()
    
    def load_settings(self):
        """Lädt Einstellungen"""
        default_settings = {
            "language": "Deutsch",
            "default_format": "{20|fkud|Schwarz}",
            "toolbar_position": "Oben"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_settings
        return default_settings
    
    def init_ui(self):
        """Initialisiert die UI"""
        lang = self.settings["language"]
        self.setWindowTitle("DuckDiary - Editor" if lang == "English" else "Tagesgans - Bearbeitungsmodus")
        self.setMinimumSize(900, 700)
        
        # Icon
        icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Hauptlayout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # Tagebuch-Auswahl
        if self.mode == "edit":
            diary_layout = QHBoxLayout()
            diary_label = QLabel("Tagebuch:" if lang == "Deutsch" else "Diary:")
            self.diary_combo = QComboBox()
            self.diary_combo.currentIndexChanged.connect(self.on_diary_selected)
            
            new_entry_btn = QPushButton("Neuer Eintrag" if lang == "Deutsch" else "New Entry")
            new_entry_btn.clicked.connect(self.new_entry)
            
            diary_layout.addWidget(diary_label)
            diary_layout.addWidget(self.diary_combo)
            diary_layout.addWidget(new_entry_btn)
            main_layout.addLayout(diary_layout)
            
            # Eintrags-Liste
            self.entry_list = QListWidget()
            self.entry_list.itemClicked.connect(self.on_entry_selected)
            main_layout.addWidget(self.entry_list)
        
        # Text-Editor
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptDrops(True)
        self.text_edit.dragEnterEvent = self.drag_enter_event
        self.text_edit.dropEvent = self.drop_event
        main_layout.addWidget(self.text_edit)
        
        # Speichern Button
        save_btn = QPushButton("Speichern" if lang == "Deutsch" else "Save")
        save_btn.clicked.connect(self.save_entry)
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-size: 14px;")
        main_layout.addWidget(save_btn)
        
        central_widget.setLayout(main_layout)
        
        # Toolbar erstellen
        self.create_toolbar()
    
    def create_toolbar(self):
        """Erstellt die Formatierungs-Toolbar"""
        toolbar = QToolBar("Formatierung")
        
        # Position der Toolbar
        pos = self.settings.get("toolbar_position", "Oben")
        if pos == "Oben":
            self.addToolBar(Qt.TopToolBarArea, toolbar)
        elif pos == "Unten":
            self.addToolBar(Qt.BottomToolBarArea, toolbar)
        elif pos == "Links":
            self.addToolBar(Qt.LeftToolBarArea, toolbar)
        else:  # Rechts
            self.addToolBar(Qt.RightToolBarArea, toolbar)
        
        # Schriftgröße
        toolbar.addWidget(QLabel("Größe:"))
        self.size_spin = QSpinBox()
        self.size_spin.setMinimum(8)
        self.size_spin.setMaximum(72)
        self.size_spin.setValue(20)
        self.size_spin.valueChanged.connect(self.apply_formatting)
        toolbar.addWidget(self.size_spin)
        
        # Fett
        self.bold_action = QAction("B", self)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.apply_formatting)
        font = self.bold_action.font()
        font.setBold(True)
        self.bold_action.setFont(font)
        toolbar.addAction(self.bold_action)
        
        # Kursiv
        self.italic_action = QAction("I", self)
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self.apply_formatting)
        font = self.italic_action.font()
        font.setItalic(True)
        self.italic_action.setFont(font)
        toolbar.addAction(self.italic_action)
        
        # Unterstrichen
        self.underline_action = QAction("U", self)
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self.apply_formatting)
        font = self.underline_action.font()
        font.setUnderline(True)
        self.underline_action.setFont(font)
        toolbar.addAction(self.underline_action)
        
        # Durchgestrichen
        self.strike_action = QAction("S", self)
        self.strike_action.setCheckable(True)
        self.strike_action.triggered.connect(self.apply_formatting)
        toolbar.addAction(self.strike_action)
        
        # Farbe
        self.color_btn = QPushButton("Farbe")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = QColor("black")
        toolbar.addWidget(self.color_btn)
        
        toolbar.addSeparator()
        
        # Spezielle Elemente
        person_btn = QPushButton("@Person")
        person_btn.clicked.connect(self.insert_person)
        toolbar.addWidget(person_btn)
        
        place_btn = QPushButton("%Ort")
        place_btn.clicked.connect(self.insert_place)
        toolbar.addWidget(place_btn)
        
        copy_btn = QPushButton("'Copy'")
        copy_btn.clicked.connect(self.insert_copy)
        toolbar.addWidget(copy_btn)
        
        time_btn = QPushButton("§Zeit")
        time_btn.clicked.connect(self.insert_timestamp)
        toolbar.addWidget(time_btn)
        
        label_btn = QPushButton("=Label")
        label_btn.clicked.connect(self.insert_label)
        toolbar.addWidget(label_btn)
        
        media_btn = QPushButton("+ Medien")
        media_btn.clicked.connect(self.insert_media)
        toolbar.addWidget(media_btn)
    
    def apply_formatting(self):
        """Wendet Formatierung auf markierten Text an"""
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return
        
        fmt = QTextCharFormat()
        
        # Schriftgröße
        font = QFont()
        font.setPointSize(self.size_spin.value())
        font.setBold(self.bold_action.isChecked())
        font.setItalic(self.italic_action.isChecked())
        font.setUnderline(self.underline_action.isChecked())
        font.setStrikeOut(self.strike_action.isChecked())
        fmt.setFont(font)
        
        # Farbe
        fmt.setForeground(self.current_color)
        
        cursor.mergeCharFormat(fmt)
    
    def choose_color(self):
        """Farbauswahl"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.apply_formatting()
    
    def insert_person(self):
        """Fügt @Person ein"""
        name, ok = QInputDialog.getText(self, "Person", "Name:")
        if ok and name:
            # vCard-Datei auswählen
            vcard_file, _ = QFileDialog.getOpenFileName(self, "vCard auswählen", str(Path.home()), "vCard (*.vcard *.vcf)")
            if vcard_file:
                self.text_edit.insertPlainText(f"@{name}")
                # vCard für später merken (wird beim Speichern kopiert)
                if not hasattr(self, 'vcards'):
                    self.vcards = {}
                self.vcards[name] = vcard_file
    
    def insert_place(self):
        """Fügt %Ort ein"""
        name, ok = QInputDialog.getText(self, "Ort", "Ortsname:")
        if ok and name:
            # KML-Datei auswählen
            kml_file, _ = QFileDialog.getOpenFileName(self, "KML auswählen", str(Path.home()), "KML (*.kml)")
            if kml_file:
                self.text_edit.insertPlainText(f"%{name}")
                # KML für später merken
                if not hasattr(self, 'kmls'):
                    self.kmls = {}
                self.kmls[name] = kml_file
    
    def insert_copy(self):
        """Fügt 'Text' für Easy Copy ein"""
        text, ok = QInputDialog.getText(self, "Easy Copy", "Text:")
        if ok and text:
            self.text_edit.insertPlainText(f"'{text}'")
    
    def insert_timestamp(self):
        """Fügt §Zeitstempel ein"""
        dialog = DatePickerDialog(self, self.settings["language"])
        if dialog.exec_() == QDialog.Accepted:
            date = dialog.get_date()
            # Zeit hinzufügen
            time, ok = QInputDialog.getText(self, "Uhrzeit", "Uhrzeit (HH:MM):", text="12:00")
            if ok:
                try:
                    hour, minute = map(int, time.split(':'))
                    timestamp = f"§{date.year}.{date.month:02d}.{date.day:02d}.{hour:02d}.{minute:02d}"
                    self.text_edit.insertPlainText(timestamp)
                except:
                    pass
    
    def insert_label(self):
        """Fügt =Label ein"""
        label, ok = QInputDialog.getText(self, "Label", "Label-Name:")
        if ok and label:
            self.text_edit.insertPlainText(f"={label}")
    
    def insert_media(self):
        """Fügt Medien ein"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Medien auswählen", 
            str(Path.home()),
            "Medien (*.png *.jpg *.jpeg *.svg *.mp3 *.ogg *.opus *.mp4)"
        )
        
        for file in files:
            filename = Path(file).name
            self.text_edit.insertPlainText(f"<{filename}>")
            
            # Datei für später merken
            if not hasattr(self, 'media_files'):
                self.media_files = []
            self.media_files.append(file)
    
    def drag_enter_event(self, event):
        """Drag Enter Event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event):
        """Drop Event für Medien"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        
        for file in files:
            file_path = Path(file)
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.mp3', '.ogg', '.opus', '.mp4']:
                filename = file_path.name
                self.text_edit.insertPlainText(f"<{filename}>")
                
                if not hasattr(self, 'media_files'):
                    self.media_files = []
                self.media_files.append(str(file_path))
    
    def scan_diaries(self):
        """Scannt nach .duckday Ordnern"""
        self.diary_combo.clear()
        home = Path.home()
        
        for duckday_dir in home.rglob("*.duckday"):
            if duckday_dir.is_dir():
                diary_name = duckday_dir.stem
                self.diary_combo.addItem(diary_name, str(duckday_dir))
    
    def on_diary_selected(self, index):
        """Wird aufgerufen wenn ein Tagebuch ausgewählt wurde"""
        if index >= 0:
            self.current_diary = Path(self.diary_combo.itemData(index))
            self.load_entries()
    
    def load_entries(self):
        """Lädt alle Einträge"""
        self.entry_list.clear()
        
        if not self.current_diary:
            return
        
        entries = []
        for year_dir in sorted(self.current_diary.glob("*")):
            if year_dir.is_dir() and year_dir.name.isdigit():
                for month_dir in sorted(year_dir.glob("*")):
                    if month_dir.is_dir():
                        for day_dir in sorted(month_dir.glob("*")):
                            if day_dir.is_dir():
                                day_file = day_dir / "Day.txt"
                                if day_file.exists():
                                    date_str = f"{day_dir.name}.{month_dir.name}.{year_dir.name}"
                                    entries.append((date_str, day_file))
        
        for date_str, day_file in reversed(sorted(entries)):
            item = QListWidgetItem(date_str)
            item.setData(Qt.UserRole, str(day_file))
            self.entry_list.addItem(item)
    
    def on_entry_selected(self, item):
        """Lädt einen Eintrag zum Bearbeiten"""
        day_file = Path(item.data(Qt.UserRole))
        self.current_entry = day_file
        
        with open(day_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rohen Text anzeigen (könnte auch formatiert geparst werden)
        self.text_edit.setPlainText(content)
    
    def new_entry(self):
        """Erstellt einen neuen Eintrag"""
        if not self.current_diary:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie zuerst ein Tagebuch aus!")
            return
        
        dialog = DatePickerDialog(self, self.settings["language"])
        if dialog.exec_() == QDialog.Accepted:
            self.current_date = dialog.get_date()
            self.text_edit.clear()
            
            # Standardformatierung einfügen
            default_format = self.settings.get("default_format", "{20|fkud|Schwarz}")
            self.text_edit.setPlainText(default_format)
    
    def create_new_diary(self):
        """Erstellt ein neues Tagebuch"""
        dialog = CreateDiaryDialog(self, self.settings["language"])
        if dialog.exec_() == QDialog.Accepted:
            info = dialog.get_diary_info()
            
            if not info["name"]:
                QMessageBox.warning(self, "Fehler", "Bitte geben Sie einen Namen ein!")
                self.close()
                return
            
            # Tagebuch-Ordner erstellen
            diary_path = info["path"] / f"{info['name']}.duckday"
            diary_path.mkdir(parents=True, exist_ok=True)
            
            # Info.txt herunterladen
            try:
                info_url = "https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/refs/heads/main/Info.txt"
                info_file = diary_path / "Info.txt"
                urllib.request.urlretrieve(info_url, info_file)
            except:
                # Fallback: eigene Info.txt
                with open(diary_path / "Info.txt", 'w') as f:
                    f.write("This is a Tagesgans diary.\n")
            
            # Install.sh herunterladen
            try:
                install_url = "https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/refs/heads/main/Install.sh"
                install_file = diary_path / "Install.sh"
                urllib.request.urlretrieve(install_url, install_file)
                install_file.chmod(0o755)  # Ausführbar machen
            except:
                pass
            
            # Icon kopieren (wenn vorhanden)
            icon_src = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
            if icon_src.exists():
                shutil.copy(icon_src, diary_path / "Icon.png")
            
            self.current_diary = diary_path
            
            # Ersten Eintrag erstellen
            self.new_entry()
        else:
            self.close()
    
    def save_entry(self):
        """Speichert den aktuellen Eintrag"""
        if not self.current_diary:
            QMessageBox.warning(self, "Fehler", "Kein Tagebuch ausgewählt!")
            return
        
        # Datum bestimmen
        if self.current_entry:
            # Bestehenden Eintrag bearbeiten
            entry_dir = self.current_entry.parent
        else:
            # Neuer Eintrag
            if not self.current_date:
                QMessageBox.warning(self, "Fehler", "Kein Datum ausgewählt!")
                return
            
            # Ordnerstruktur erstellen
            year_dir = self.current_diary / str(self.current_date.year)
            month_dir = year_dir / self.current_date.strftime("%B")
            day_dir = month_dir / f"{self.current_date.day:02d}"
            entry_dir = day_dir
            entry_dir.mkdir(parents=True, exist_ok=True)
        
        # Day.txt speichern
        day_file = entry_dir / "Day.txt"
        content = self.text_edit.toPlainText()
        
        with open(day_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # vCards kopieren
        if hasattr(self, 'vcards'):
            for name, vcard_file in self.vcards.items():
                shutil.copy(vcard_file, entry_dir / f"{name}.vcard")
            self.vcards = {}
        
        # KMLs kopieren
        if hasattr(self, 'kmls'):
            for name, kml_file in self.kmls.items():
                shutil.copy(kml_file, entry_dir / f"{name}.kml")
            self.kmls = {}
        
        # Medien kopieren
        if hasattr(self, 'media_files'):
            for media_file in self.media_files:
                shutil.copy(media_file, entry_dir / Path(media_file).name)
            self.media_files = []
        
        QMessageBox.information(self, "Gespeichert", "Eintrag wurde gespeichert!")
        
        # Liste aktualisieren
        if self.mode == "edit":
            self.load_entries()


def main():
    if len(sys.argv) < 2:
        print("Usage: editor.py <config_file> [edit|create]")
        sys.exit(1)
    
    mode = sys.argv[2] if len(sys.argv) > 2 else "edit"
    
    app = QApplication(sys.argv)
    app.setApplicationName("DuckDiary")
    
    editor = DiaryEditor(sys.argv[1], mode)
    editor.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Editor - DuckDiary
Creates and edits diary entries
Version: 0.0.2
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
                             QCalendarWidget, QLineEdit, QInputDialog, QPlainTextEdit)
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
        
        # Einfachere Navigation: Klick auf Jahr/Monat
        self.calendar.setNavigationBarVisible(True)
        # Erlaube direktes Springen zu Jahr/Monat
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
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
        self.icon_path = None
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
        
        # Icon-Auswahl
        icon_layout = QHBoxLayout()
        self.icon_label = QLabel("Kein Icon" if self.language == "Deutsch" else "No Icon")
        icon_browse_btn = QPushButton("Icon wählen..." if self.language == "Deutsch" else "Choose Icon...")
        icon_browse_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(self.icon_label)
        icon_layout.addWidget(icon_browse_btn)
        
        layout.addRow("Icon:" if self.language == "English" else "Icon:", icon_layout)
        
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
    
    def browse_icon(self):
        """Icon auswählen"""
        icon_file, _ = QFileDialog.getOpenFileName(
            self, 
            "Icon auswählen" if self.language == "Deutsch" else "Choose Icon",
            str(Path.home()),
            "Bilder (*.png *.jpg *.jpeg *.svg)"
        )
        if icon_file:
            self.icon_path = icon_file
            self.icon_label.setText(Path(icon_file).name)
    
    def get_diary_info(self):
        """Gibt Tagebuch-Informationen zurück"""
        return {
            "name": self.name_edit.text(),
            "path": Path(self.path_edit.text()),
            "icon": self.icon_path
        }


class DiaryEditor(QMainWindow):
    """Hauptfenster des Tagebuch-Editors"""
    
    def __init__(self, config_file, mode="edit"):
        super().__init__()
        self.config_file = Path(config_file)
        self.settings = self.load_settings()
        self.mode = mode
        self.current_diary = None
        self.current_entry = None
        self.current_date = None
        
        # Für Markup-Tracking
        self.vcards = {}
        self.kmls = {}
        self.media_files = []
        
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
                    loaded = json.load(f)
                    default_settings.update(loaded)
                    return default_settings
            except Exception as e:
                print(f"Fehler beim Laden der Config: {e}")
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
        
        # Text-Editor - PLAINTEXT für Markup!
        self.text_edit = QPlainTextEdit()
        self.text_edit.setAcceptDrops(True)
        self.text_edit.dragEnterEvent = self.drag_enter_event
        self.text_edit.dropEvent = self.drop_event
        
        # Monospace Font für Markup
        font = QFont("Monospace", 12)
        self.text_edit.setFont(font)
        
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
        else:
            self.addToolBar(Qt.RightToolBarArea, toolbar)
        
        # Format einfügen
        format_btn = QPushButton("Format")
        format_btn.clicked.connect(self.insert_format)
        toolbar.addWidget(format_btn)
        
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
    
    def insert_format(self):
        """Fügt Format-Tag ein"""
        # Dialog für Format-Einstellungen
        dialog = QDialog(self)
        dialog.setWindowTitle("Format einfügen")
        layout = QFormLayout()
        
        size_spin = QSpinBox()
        size_spin.setMinimum(8)
        size_spin.setMaximum(72)
        size_spin.setValue(20)
        layout.addRow("Größe:", size_spin)
        
        # FKUD Checkboxen
        bold_check = QDialog()
        bold_widget = QWidget()
        bold_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QCheckBox
        fett_check = QCheckBox("Fett (F)")
        kursiv_check = QCheckBox("Kursiv (K)")
        unterstrichen_check = QCheckBox("Unterstrichen (U)")
        durchgestrichen_check = QCheckBox("Durchgestrichen (D)")
        
        style_layout = QVBoxLayout()
        style_layout.addWidget(fett_check)
        style_layout.addWidget(kursiv_check)
        style_layout.addWidget(unterstrichen_check)
        style_layout.addWidget(durchgestrichen_check)
        layout.addRow("Stil:", style_layout)
        
        # Farbe
        colors = ["Schwarz", "Rot", "Grün", "Blau", "Gelb", "Orange", "Lila", "Grau"]
        color_combo = QComboBox()
        color_combo.addItems(colors)
        layout.addRow("Farbe:", color_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(button_box)
        dialog.setLayout(main_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            size = size_spin.value()
            style = ""
            style += "F" if fett_check.isChecked() else "f"
            style += "K" if kursiv_check.isChecked() else "k"
            style += "U" if unterstrichen_check.isChecked() else "u"
            style += "D" if durchgestrichen_check.isChecked() else "d"
            color = color_combo.currentText()
            
            format_tag = f"{{{size}|{style}|{color}}}"
            self.text_edit.insertPlainText(format_tag)
    
    def insert_person(self):
        """Fügt @Person ein"""
        name, ok = QInputDialog.getText(self, "Person", "Name:")
        if ok and name:
            vcard_file, _ = QFileDialog.getOpenFileName(
                self, "vCard auswählen", str(Path.home()), "vCard (*.vcard *.vcf)"
            )
            if vcard_file:
                self.text_edit.insertPlainText(f"@{name}")
                self.vcards[name] = vcard_file
    
    def insert_place(self):
        """Fügt %Ort ein"""
        name, ok = QInputDialog.getText(self, "Ort", "Ortsname:")
        if ok and name:
            kml_file, _ = QFileDialog.getOpenFileName(
                self, "KML auswählen", str(Path.home()), "KML (*.kml)"
            )
            if kml_file:
                self.text_edit.insertPlainText(f"%{name}")
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
            time, ok = QInputDialog.getText(
                self, "Uhrzeit", "Uhrzeit (HH:MM):", text="12:00"
            )
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
            self.text_edit.setPlainText(default_format + "\n")
    
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
                with open(diary_path / "Info.txt", 'w') as f:
                    f.write("This is a Tagesgans diary.\n")
            
            # Install.sh herunterladen
            try:
                install_url = "https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/refs/heads/main/Install.sh"
                install_file = diary_path / "Install.sh"
                urllib.request.urlretrieve(install_url, install_file)
                install_file.chmod(0o755)
            except:
                pass
            
            # Icon kopieren
            if info["icon"]:
                shutil.copy(info["icon"], diary_path / "Icon.png")
            else:
                # Standard-Icon verwenden
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
            entry_dir = self.current_entry.parent
        else:
            if not self.current_date:
                QMessageBox.warning(self, "Fehler", "Kein Datum ausgewählt!")
                return
            
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
        for name, vcard_file in self.vcards.items():
            shutil.copy(vcard_file, entry_dir / f"{name}.vcard")
        self.vcards = {}
        
        # KMLs kopieren
        for name, kml_file in self.kmls.items():
            shutil.copy(kml_file, entry_dir / f"{name}.kml")
        self.kmls = {}
        
        # Medien kopieren
        for media_file in self.media_files:
            shutil.copy(media_file, entry_dir / Path(media_file).name)
        self.media_files = []
        
        QMessageBox.information(self, "Gespeichert", "Eintrag wurde gespeichert!")
        
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

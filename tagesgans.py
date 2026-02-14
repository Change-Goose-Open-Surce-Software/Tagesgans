#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans - Day Goose Diary System
Main Program
Version: 0.0.2
Released: 14.02.2026
Author: Change Goose
License: MIT
"""

import sys
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QDialog, QComboBox, QFormLayout,
                             QDialogButtonBox, QMessageBox, QTextBrowser, QSpinBox,
                             QHBoxLayout, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QCheckBox

class SettingsDialog(QDialog):
    """Einstellungsdialog für Tagesgans"""
    
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings or {}
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(self.tr("Einstellungen"))
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # Sprache
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Deutsch", "English"])
        current_lang = self.settings.get("language", "Deutsch")
        self.language_combo.setCurrentText(current_lang)
        layout.addRow(self.tr("Sprache:"), self.language_combo)
        
        # Standardformatierung - ERWEITERT
        format_layout = QVBoxLayout()
        
        # Schriftgröße
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Größe:"))
        self.size_spin = QSpinBox()
        self.size_spin.setMinimum(8)
        self.size_spin.setMaximum(72)
        
        # Parse current format
        current_format = self.settings.get("default_format", "{20|fkud|Schwarz}")
        try:
            import re
            match = re.match(r'\{(\d+)\|([FfKkUuDd]{4})\|([^}]+)\}', current_format)
            if match:
                self.size_spin.setValue(int(match.group(1)))
                style = match.group(2)
                color = match.group(3)
            else:
                self.size_spin.setValue(20)
                style = "fkud"
                color = "Schwarz"
        except:
            self.size_spin.setValue(20)
            style = "fkud"
            color = "Schwarz"
        
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()
        format_layout.addLayout(size_layout)
        
        # FKUD Checkboxen
        fkud_layout = QHBoxLayout()
        self.fett_check = QCheckBox("Fett (F)")
        self.kursiv_check = QCheckBox("Kursiv (K)")
        self.unterstrichen_check = QCheckBox("Unterstrichen (U)")
        self.durchgestrichen_check = QCheckBox("Durchgestrichen (D)")
        
        self.fett_check.setChecked('F' in style)
        self.kursiv_check.setChecked('K' in style)
        self.unterstrichen_check.setChecked('U' in style)
        self.durchgestrichen_check.setChecked('D' in style)
        
        fkud_layout.addWidget(self.fett_check)
        fkud_layout.addWidget(self.kursiv_check)
        fkud_layout.addWidget(self.unterstrichen_check)
        fkud_layout.addWidget(self.durchgestrichen_check)
        format_layout.addLayout(fkud_layout)
        
        # Farbe
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Farbe:"))
        self.color_combo = QComboBox()
        colors = ["Schwarz", "Rot", "Grün", "Blau", "Gelb", "Orange", "Lila", "Grau", "Weiß"]
        self.color_combo.addItems(colors)
        self.color_combo.setCurrentText(color)
        color_layout.addWidget(self.color_combo)
        color_layout.addStretch()
        format_layout.addLayout(color_layout)
        
        layout.addRow(self.tr("Standardformatierung:"), format_layout)
        
        # Bearbeitungsleiste Position (Editor)
        self.toolbar_pos = QComboBox()
        self.toolbar_pos.addItems(["Oben", "Unten", "Rechts", "Links"])
        current_toolbar = self.settings.get("toolbar_position", "Oben")
        self.toolbar_pos.setCurrentText(current_toolbar)
        layout.addRow(self.tr("Bearbeitungsleiste:"), self.toolbar_pos)
        
        # EINE Seitenleiste Position (Reader) - vereinfacht
        self.sidebar_pos = QComboBox()
        self.sidebar_pos.addItems(["Rechts", "Links"])
        current_sidebar = self.settings.get("sidebar_position", "Rechts")
        self.sidebar_pos.setCurrentText(current_sidebar)
        layout.addRow(self.tr("Seitenleiste (Reader):"), self.sidebar_pos)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
        
    def get_settings(self):
        """Gibt die aktuellen Einstellungen zurück"""
        # Format zusammenbauen
        size = self.size_spin.value()
        style = ""
        style += "F" if self.fett_check.isChecked() else "f"
        style += "K" if self.kursiv_check.isChecked() else "k"
        style += "U" if self.unterstrichen_check.isChecked() else "u"
        style += "D" if self.durchgestrichen_check.isChecked() else "d"
        color = self.color_combo.currentText()
        
        default_format = f"{{{size}|{style}|{color}}}"
        
        return {
            "language": self.language_combo.currentText(),
            "default_format": default_format,
            "toolbar_position": self.toolbar_pos.currentText(),
            "sidebar_position": self.sidebar_pos.currentText()
        }
    
    def tr(self, text):
        """Simple translation helper"""
        translations = {
            "Einstellungen": "Settings" if self.settings.get("language") == "English" else "Einstellungen",
            "Sprache:": "Language:" if self.settings.get("language") == "English" else "Sprache:",
            "Standardformatierung:": "Default Formatting:" if self.settings.get("language") == "English" else "Standardformatierung:",
            "Bearbeitungsleiste:": "Toolbar Position:" if self.settings.get("language") == "English" else "Bearbeitungsleiste:",
            "Seitenleiste (Reader):": "Sidebar (Reader):" if self.settings.get("language") == "English" else "Seitenleiste (Reader):"
        }
        return translations.get(text, text)


class TutorialDialog(QDialog):
    """Tutorial/Einführung für Tagesgans"""
    
    def __init__(self, parent=None, language="Deutsch"):
        super().__init__(parent)
        self.language = language
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Tutorial - Tagesgans")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        tutorial_text = QTextBrowser()
        tutorial_text.setOpenExternalLinks(True)
        
        if self.language == "Deutsch":
            content = """
            <h2>Willkommen bei Tagesgans!</h2>
            <p>Tagesgans ist ein flexibles Tagebuch-System mit erweiterten Funktionen.</p>
            
            <h3>Erste Schritte:</h3>
            <ol>
                <li><b>Tagebuch erstellen:</b> Erstelle ein neues Tagebuch mit eigenem Namen und Speicherort</li>
                <li><b>Einträge schreiben:</b> Nutze den Editor um formatierte Einträge zu erstellen</li>
                <li><b>Einträge lesen:</b> Der Reader zeigt deine Einträge übersichtlich an</li>
            </ol>
            
            <h3>Besondere Funktionen:</h3>
            <ul>
                <li><b>@Personen:</b> Erwähne Personen mit @Name (speichert vCard)</li>
                <li><b>%Orte:</b> Pinne Orte mit %Ort (speichert KML für QGIS)</li>
                <li><b>'Text':</b> Text in ' ' kann einfach kopiert werden</li>
                <li><b>§Zeitstempel:</b> §2026.02.14.10.30 für Termine</li>
                <li><b>=Labels:</b> Organisiere mit =Label</li>
                <li><b>Medien:</b> Füge Bilder, Videos und Audio hinzu</li>
            </ul>
            
            <h3>Formatierung:</h3>
            <p>Der Editor bietet eine komfortable Formatierungsleiste. Du kannst Text markieren 
            und dann Schriftgröße, Farbe, Fett, Kursiv, Unterstrichen und Durchgestrichen einstellen.</p>
            
            <h3>Tagebuch-Struktur:</h3>
            <p>Tagebücher werden als Ordner mit .duckday Endung gespeichert. 
            Die Struktur ist: Jahr/Monat/Tag/Day.txt</p>
            """
        else:
            content = """
            <h2>Welcome to Tagesgans!</h2>
            <p>Tagesgans is a flexible diary system with advanced features.</p>
            
            <h3>Getting Started:</h3>
            <ol>
                <li><b>Create Diary:</b> Create a new diary with custom name and location</li>
                <li><b>Write Entries:</b> Use the editor to create formatted entries</li>
                <li><b>Read Entries:</b> The reader displays your entries clearly</li>
            </ol>
            
            <h3>Special Features:</h3>
            <ul>
                <li><b>@People:</b> Mention people with @Name (stores vCard)</li>
                <li><b>%Places:</b> Pin places with %Place (stores KML for QGIS)</li>
                <li><b>'Text':</b> Text in ' ' can be easily copied</li>
                <li><b>§Timestamps:</b> §2026.02.14.10.30 for appointments</li>
                <li><b>=Labels:</b> Organize with =Label</li>
                <li><b>Media:</b> Add images, videos and audio</li>
            </ul>
            
            <h3>Formatting:</h3>
            <p>The editor provides a comfortable formatting toolbar. You can mark text 
            and then set font size, color, bold, italic, underline and strikethrough.</p>
            
            <h3>Diary Structure:</h3>
            <p>Diaries are stored as folders with .duckday extension. 
            The structure is: Year/Month/Day/Day.txt</p>
            """
        
        tutorial_text.setHtml(content)
        layout.addWidget(tutorial_text)
        
        close_button = QPushButton("Schließen" if self.language == "Deutsch" else "Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)


class AboutDialog(QDialog):
    """Über Tagesgans Dialog"""
    
    def __init__(self, parent=None, language="Deutsch"):
        super().__init__(parent)
        self.language = language
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Über Tagesgans" if self.language == "Deutsch" else "About Tagesgans")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
        
        if self.language == "Deutsch":
            content = """
            <h2>Tagesgans - Day Goose Diary</h2>
            <p><b>Version:</b> 0.0.2<br>
            <b>Veröffentlicht:</b> 14.02.2026<br>
            <b>Autor:</b> Change Goose<br>
            <b>Lizenz:</b> MIT License</p>
            
            <h3>Über das Projekt:</h3>
            <p>Tagesgans ist ein Open-Source Tagebuch-System mit erweiterten Funktionen
            für Formatierung, Multimedia-Integration und Kontextverlinkung.</p>
            
            <h3>Links:</h3>
            <p><b>GitHub:</b> <a href="https://github.com/Change-Goose-Open-Surce-Software/Tagesgans/">
            github.com/Change-Goose-Open-Surce-Software/Tagesgans/</a></p>
            
            <h3>RSS Feeds:</h3>
            <p>tagesgans.xml<br>
            change-goose.xml</p>
            
            <h3>Entwickelt mit Hilfe von:</h3>
            <p>Coding KI Assistenz</p>
            
            <p><i>Letztes Update: 14.02.2026</i></p>
            """
        else:
            content = """
            <h2>Tagesgans - Day Goose Diary</h2>
            <p><b>Version:</b> 0.0.2<br>
            <b>Released:</b> 14.02.2026<br>
            <b>Author:</b> Change Goose<br>
            <b>License:</b> MIT License</p>
            
            <h3>About the Project:</h3>
            <p>Tagesgans is an open-source diary system with advanced features
            for formatting, multimedia integration and context linking.</p>
            
            <h3>Links:</h3>
            <p><b>GitHub:</b> <a href="https://github.com/Change-Goose-Open-Surce-Software/Tagesgans/">
            github.com/Change-Goose-Open-Surce-Software/Tagesgans/</a></p>
            
            <h3>RSS Feeds:</h3>
            <p>tagesgans.xml<br>
            change-goose.xml</p>
            
            <h3>Developed with help from:</h3>
            <p>Coding AI Assistance</p>
            
            <p><i>Last Update: 14.02.2026</i></p>
            """
        
        about_text.setHtml(content)
        layout.addWidget(about_text)
        
        close_button = QPushButton("Schließen" if self.language == "Deutsch" else "Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)


class TagesgansMain(QMainWindow):
    """Hauptfenster von Tagesgans"""
    
    def __init__(self):
        super().__init__()
        self.config_file = Path.home() / ".config" / "tagesgans.txt"
        self.settings = self.load_settings()
        
        # Erststart Check
        if not self.config_file.exists():
            self.first_run_setup()
        
        self.init_ui()
        
    def load_settings(self):
        """Lädt die Einstellungen aus der Konfigurationsdatei"""
        default_settings = {
            "language": "Deutsch",
            "default_format": "{20|fkud|Schwarz}",
            "toolbar_position": "Oben",
            "sidebar_position": "Rechts"
        }
        
        # Config-Verzeichnis erstellen falls nicht vorhanden
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge mit defaults für fehlende Keys
                    default_settings.update(loaded)
                    return default_settings
            except Exception as e:
                print(f"Fehler beim Laden der Config: {e}")
                return default_settings
        return default_settings
    
    def save_settings(self):
        """Speichert die Einstellungen"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            print(f"Settings gespeichert in: {self.config_file}")
        except Exception as e:
            print(f"Fehler beim Speichern der Config: {e}")
    
    def first_run_setup(self):
        """Erstkonfiguration beim ersten Start"""
        msg = QMessageBox()
        msg.setWindowTitle("Willkommen bei Tagesgans!")
        msg.setText("Willkommen bei Tagesgans!\n\nDies ist der erste Start. "
                   "Möchten Sie jetzt die Einstellungen konfigurieren?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec_() == QMessageBox.Yes:
            self.open_settings()
        else:
            self.save_settings()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("Tagesgans - Day Goose Diary")
        self.setMinimumSize(600, 500)
        
        # Icon setzen
        icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Titel
        title_label = QLabel("Tagesgans")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Day Goose Diary System" if self.settings["language"] == "English" else "Tagebuch-System")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # Hauptbuttons
        if self.settings["language"] == "Deutsch":
            read_btn = self.create_button("📖 Tagebuch lesen", self.read_diary)
            edit_btn = self.create_button("✏️ Tagebuch bearbeiten", self.edit_diary)
            create_btn = self.create_button("➕ Tagebuch erstellen", self.create_diary)
            settings_btn = self.create_button("⚙️ Einstellungen", self.open_settings)
            tutorial_btn = self.create_button("📚 Tutorial", self.show_tutorial)
            about_btn = self.create_button("ℹ️ Über Tagesgans", self.show_about)
        else:
            read_btn = self.create_button("📖 Read Diary", self.read_diary)
            edit_btn = self.create_button("✏️ Edit Diary", self.edit_diary)
            create_btn = self.create_button("➕ Create Diary", self.create_diary)
            settings_btn = self.create_button("⚙️ Settings", self.open_settings)
            tutorial_btn = self.create_button("📚 Tutorial", self.show_tutorial)
            about_btn = self.create_button("ℹ️ About Tagesgans", self.show_about)
        
        for btn in [read_btn, edit_btn, create_btn, settings_btn, tutorial_btn, about_btn]:
            layout.addWidget(btn)
        
        layout.addStretch()
        
        central_widget.setLayout(layout)
    
    def create_button(self, text, callback):
        """Erstellt einen Button"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setMinimumHeight(50)
        btn_font = QFont()
        btn_font.setPointSize(11)
        btn.setFont(btn_font)
        return btn
    
    def read_diary(self):
        """Startet den Reader"""
        reader_path = Path(__file__).parent / "reader.py"
        if reader_path.exists():
            os.system(f"python3 '{reader_path}' '{self.config_file}' &")
        else:
            QMessageBox.warning(self, "Fehler", "reader.py nicht gefunden!")
    
    def edit_diary(self):
        """Startet den Editor zum Bearbeiten"""
        editor_path = Path(__file__).parent / "editor.py"
        if editor_path.exists():
            os.system(f"python3 '{editor_path}' '{self.config_file}' edit &")
        else:
            QMessageBox.warning(self, "Fehler", "editor.py nicht gefunden!")
    
    def create_diary(self):
        """Startet den Editor zum Erstellen"""
        editor_path = Path(__file__).parent / "editor.py"
        if editor_path.exists():
            os.system(f"python3 '{editor_path}' '{self.config_file}' create &")
        else:
            QMessageBox.warning(self, "Fehler", "editor.py nicht gefunden!")
    
    def open_settings(self):
        """Öffnet den Einstellungsdialog"""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.save_settings()
            # UI aktualisieren
            self.init_ui()
    
    def show_tutorial(self):
        """Zeigt das Tutorial"""
        dialog = TutorialDialog(self, self.settings["language"])
        dialog.exec_()
    
    def show_about(self):
        """Zeigt die Über-Information"""
        dialog = AboutDialog(self, self.settings["language"])
        dialog.exec_()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tagesgans")
    
    window = TagesgansMain()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

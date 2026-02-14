#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Reader - DiaryDuck
Reads and displays diary entries
Version: 0.0.1
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QTextBrowser, QSplitter,
                             QFileDialog, QListWidgetItem, QDockWidget, QMessageBox,
                             QCalendarWidget, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QUrl, QDate
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QDesktopServices, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


class CalendarDialog(QDialog):
    """Dialog zum Anzeigen eines Datums im Kalender"""
    
    def __init__(self, parent=None, date_str=None):
        super().__init__(parent)
        self.setWindowTitle("Kalender")
        self.init_ui(date_str)
    
    def init_ui(self, date_str):
        layout = QVBoxLayout()
        
        calendar = QCalendarWidget()
        
        if date_str:
            # Parse §Jahr.Monat.Tag.Stunde.Minute
            try:
                parts = date_str.split('.')
                if len(parts) >= 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    calendar.setSelectedDate(QDate(year, month, day))
            except:
                pass
        
        layout.addWidget(calendar)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class DiaryReader(QMainWindow):
    """Hauptfenster des Tagebuch-Readers"""
    
    def __init__(self, config_file):
        super().__init__()
        self.config_file = Path(config_file)
        self.settings = self.load_settings()
        self.current_diary = None
        self.current_entry = None
        self.labels = []
        self.timestamps = []
        
        self.init_ui()
        self.scan_diaries()
    
    def load_settings(self):
        """Lädt Einstellungen"""
        default_settings = {
            "language": "Deutsch",
            "label_sidebar": "Rechts",
            "time_sidebar": "Links"
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
        self.setWindowTitle("DiaryDuck - Reader" if lang == "English" else "Tagesgans - Lesemodus")
        self.setMinimumSize(1000, 700)
        
        # Icon
        icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Hauptlayout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # Tagebuch-Auswahl
        diary_layout = QHBoxLayout()
        diary_label = QLabel("Tagebuch:" if lang == "Deutsch" else "Diary:")
        self.diary_list = QListWidget()
        self.diary_list.itemClicked.connect(self.on_diary_selected)
        
        diary_layout.addWidget(diary_label)
        diary_layout.addWidget(self.diary_list)
        main_layout.addLayout(diary_layout)
        
        # Splitter für Einträge und Inhalt
        splitter = QSplitter(Qt.Horizontal)
        
        # Eintrags-Liste
        self.entry_list = QListWidget()
        self.entry_list.itemClicked.connect(self.on_entry_selected)
        splitter.addWidget(self.entry_list)
        
        # Text-Browser für Inhalt
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenLinks(False)
        self.text_browser.anchorClicked.connect(self.on_link_clicked)
        splitter.addWidget(self.text_browser)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Seitenleisten
        self.create_sidebars()
    
    def create_sidebars(self):
        """Erstellt die Label- und Zeit-Seitenleisten"""
        lang = self.settings["language"]
        
        # Label-Seitenleiste
        self.label_dock = QDockWidget("Labels" if lang == "English" else "Labels", self)
        self.label_list = QListWidget()
        self.label_list.itemClicked.connect(self.on_label_clicked)
        self.label_dock.setWidget(self.label_list)
        
        label_pos = self.settings["label_sidebar"]
        if label_pos == "Rechts":
            self.addDockWidget(Qt.RightDockWidgetArea, self.label_dock)
        else:
            self.addDockWidget(Qt.LeftDockWidgetArea, self.label_dock)
        
        # Zeit-Seitenleiste
        self.time_dock = QDockWidget("Zeitstempel" if lang == "Deutsch" else "Timestamps", self)
        self.time_list = QListWidget()
        self.time_list.itemClicked.connect(self.on_timestamp_clicked)
        self.time_dock.setWidget(self.time_list)
        
        time_pos = self.settings["time_sidebar"]
        if time_pos == "Rechts":
            self.addDockWidget(Qt.RightDockWidgetArea, self.time_dock)
        else:
            self.addDockWidget(Qt.LeftDockWidgetArea, self.time_dock)
    
    def scan_diaries(self):
        """Scannt nach .duckday Ordnern"""
        self.diary_list.clear()
        home = Path.home()
        
        # Rekursiv nach .duckday Ordnern suchen
        for duckday_dir in home.rglob("*.duckday"):
            if duckday_dir.is_dir():
                diary_name = duckday_dir.stem  # Name ohne .duckday
                item = QListWidgetItem(diary_name)
                item.setData(Qt.UserRole, str(duckday_dir))
                
                # Icon laden wenn vorhanden
                icon_file = duckday_dir / "Icon.png"
                if icon_file.exists():
                    item.setIcon(QIcon(str(icon_file)))
                
                self.diary_list.addItem(item)
    
    def on_diary_selected(self, item):
        """Wird aufgerufen wenn ein Tagebuch ausgewählt wurde"""
        self.current_diary = Path(item.data(Qt.UserRole))
        self.load_entries()
    
    def load_entries(self):
        """Lädt alle Einträge des ausgewählten Tagebuchs"""
        self.entry_list.clear()
        
        if not self.current_diary:
            return
        
        # Alle Day.txt Dateien finden
        entries = []
        for year_dir in sorted(self.current_diary.glob("*")):
            if year_dir.is_dir() and year_dir.name.isdigit():
                for month_dir in sorted(year_dir.glob("*")):
                    if month_dir.is_dir():
                        for day_dir in sorted(month_dir.glob("*")):
                            if day_dir.is_dir():
                                day_file = day_dir / "Day.txt"
                                if day_file.exists():
                                    # Datum formatieren
                                    date_str = f"{day_dir.name}.{month_dir.name}.{year_dir.name}"
                                    entries.append((date_str, day_file))
        
        # Sortiert hinzufügen (neueste zuerst)
        for date_str, day_file in reversed(sorted(entries)):
            item = QListWidgetItem(date_str)
            item.setData(Qt.UserRole, str(day_file))
            self.entry_list.addItem(item)
    
    def on_entry_selected(self, item):
        """Wird aufgerufen wenn ein Eintrag ausgewählt wurde"""
        day_file = Path(item.data(Qt.UserRole))
        self.load_entry(day_file)
    
    def load_entry(self, day_file):
        """Lädt und zeigt einen Tagebucheintrag"""
        self.current_entry = day_file
        self.labels = []
        self.timestamps = []
        self.label_list.clear()
        self.time_list.clear()
        
        if not day_file.exists():
            return
        
        with open(day_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Content parsen und anzeigen
        self.display_content(content, day_file.parent)
    
    def display_content(self, content, media_dir):
        """Zeigt formatierten Inhalt an"""
        self.text_browser.clear()
        cursor = self.text_browser.textCursor()
        
        # Zeile für Zeile parsen
        lines = content.split('\n')
        current_format = None
        
        for line in lines:
            if not line.strip():
                cursor.insertText('\n')
                continue
            
            # Format am Zeilenanfang?
            format_match = re.match(r'\{(\d+)\|([FfKkUuDd]{4})\|([^}]+)\}', line)
            if format_match:
                size = int(format_match.group(1))
                style = format_match.group(2)
                color = format_match.group(3)
                current_format = (size, style, color)
                line = line[format_match.end():]
            
            if current_format:
                self.insert_formatted_line(cursor, line, current_format, media_dir)
            else:
                cursor.insertText(line + '\n')
        
        # Labels und Zeitstempel in Seitenleisten
        for label in self.labels:
            self.label_list.addItem(label)
        
        for ts in self.timestamps:
            self.time_list.addItem(ts)
    
    def insert_formatted_line(self, cursor, line, format_info, media_dir):
        """Fügt eine formatierte Zeile ein"""
        size, style, color = format_info
        
        # Text-Format erstellen
        char_format = QTextCharFormat()
        font = QFont()
        font.setPointSize(size)
        font.setBold('F' in style)
        font.setItalic('K' in style)
        font.setUnderline('U' in style)
        font.setStrikeOut('D' in style)
        char_format.setFont(font)
        
        # Farbe setzen
        char_format.setForeground(QColor(color))
        
        # Zeile parsen für spezielle Elemente
        pos = 0
        while pos < len(line):
            # @Person (vCard)
            person_match = re.match(r'@(\w+)', line[pos:])
            if person_match:
                person_name = person_match.group(1)
                # Als Link einfügen
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("blue"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"person:{person_name}")
                cursor.insertText(person_name, link_format)
                pos += person_match.end()
                continue
            
            # %Ort (KML)
            place_match = re.match(r'%(\w+)', line[pos:])
            if place_match:
                place_name = place_match.group(1)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("green"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"place:{place_name}")
                cursor.insertText(place_name, link_format)
                pos += place_match.end()
                continue
            
            # 'Text' (Easy Copy)
            copy_match = re.match(r"'([^']+)'", line[pos:])
            if copy_match:
                copy_text = copy_match.group(1)
                link_format = QTextCharFormat(char_format)
                link_format.setBackground(QColor("#ffffcc"))
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"copy:{copy_text}")
                cursor.insertText(copy_text, link_format)
                pos += copy_match.end()
                continue
            
            # §Zeitstempel
            time_match = re.match(r'§([\d.]+)', line[pos:])
            if time_match:
                timestamp = time_match.group(1)
                self.timestamps.append(timestamp)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("purple"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"time:{timestamp}")
                cursor.insertText(timestamp, link_format)
                pos += time_match.end()
                continue
            
            # =Label
            label_match = re.match(r'=(\w+)', line[pos:])
            if label_match:
                label = label_match.group(1)
                if label not in self.labels:
                    self.labels.append(label)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("orange"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"label:{label}")
                cursor.insertText(f"#{label}", link_format)
                pos += label_match.end()
                continue
            
            # <Dateiname> (Media)
            media_match = re.match(r'<([^>]+)>', line[pos:])
            if media_match:
                filename = media_match.group(1)
                media_file = media_dir / filename
                if media_file.exists():
                    self.insert_media(cursor, media_file)
                pos += media_match.end()
                continue
            
            # URLs
            url_match = re.match(r'(https?://[^\s]+)', line[pos:])
            if url_match:
                url = url_match.group(1)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("blue"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(url)
                cursor.insertText(url, link_format)
                pos += url_match.end()
                continue
            
            # Normaler Text
            cursor.insertText(line[pos], char_format)
            pos += 1
        
        cursor.insertText('\n')
    
    def insert_media(self, cursor, media_file):
        """Fügt Medien ein"""
        ext = media_file.suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.svg']:
            # Bild einfügen
            cursor.insertHtml(f'<br><img src="{media_file}" width="400"><br>')
        elif ext in ['.mp3', '.ogg', '.opus', '.mp4']:
            # Medien-Link
            link_format = QTextCharFormat()
            link_format.setForeground(QColor("blue"))
            link_format.setFontUnderline(True)
            link_format.setAnchor(True)
            link_format.setAnchorHref(f"media:{media_file}")
            cursor.insertText(f"\n[{media_file.name}]\n", link_format)
    
    def on_link_clicked(self, url):
        """Behandelt Klicks auf Links"""
        url_str = url.toString()
        
        if url_str.startswith("person:"):
            # vCard öffnen
            person = url_str.split(":", 1)[1]
            vcard_file = self.current_entry.parent / f"{person}.vcard"
            if vcard_file.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(vcard_file)))
        
        elif url_str.startswith("place:"):
            # KML in QGIS öffnen
            place = url_str.split(":", 1)[1]
            kml_file = self.current_entry.parent / f"{place}.kml"
            if kml_file.exists():
                os.system(f"qgis '{kml_file}' &")
        
        elif url_str.startswith("copy:"):
            # Text in Zwischenablage kopieren
            text = url_str.split(":", 1)[1]
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Kopiert", f"'{text}' wurde in die Zwischenablage kopiert!")
        
        elif url_str.startswith("time:"):
            # Kalender öffnen
            timestamp = url_str.split(":", 1)[1]
            dialog = CalendarDialog(self, timestamp)
            dialog.exec_()
        
        elif url_str.startswith("label:"):
            # Zum Label springen (bereits sichtbar)
            pass
        
        elif url_str.startswith("media:"):
            # Media-Datei öffnen
            media_path = url_str.split(":", 1)[1]
            QDesktopServices.openUrl(QUrl.fromLocalFile(media_path))
        
        elif url_str.startswith("http"):
            # Normale URL im Browser öffnen
            QDesktopServices.openUrl(url)
    
    def on_label_clicked(self, item):
        """Springt zum Label im Text"""
        label = item.text()
        # Suche im Text
        self.text_browser.find(f"#{label}")
    
    def on_timestamp_clicked(self, item):
        """Springt zum Zeitstempel im Text"""
        timestamp = item.text()
        self.text_browser.find(timestamp)


def main():
    if len(sys.argv) < 2:
        print("Usage: reader.py <config_file>")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DiaryDuck")
    
    reader = DiaryReader(sys.argv[1])
    reader.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

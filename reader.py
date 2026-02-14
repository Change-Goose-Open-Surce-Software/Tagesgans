#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tagesgans Reader - DiaryDuck
Reads and displays diary entries
Version: 0.0.2 - Modern UI
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
                             QCalendarWidget, QDialog, QDialogButtonBox, QTreeWidget,
                             QTreeWidgetItem, QFrame, QScrollArea, QToolButton)
from PyQt5.QtCore import Qt, QUrl, QDate, QSize
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QDesktopServices, QIcon, QPalette
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


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


class EntryViewerWindow(QMainWindow):
    """Separates Fenster für Tagebucheinträge"""
    
    def __init__(self, day_file, settings, parent=None):
        super().__init__(parent)
        self.day_file = day_file
        self.settings = settings
        self.labels = []
        self.timestamps = []
        
        self.init_ui()
        self.load_entry()
    
    def init_ui(self):
        """Initialisiert die UI"""
        # Datum aus Pfad extrahieren
        parts = self.day_file.parts
        try:
            day = parts[-2]
            month = parts[-3]
            year = parts[-4]
            date_str = f"{day}.{month}.{year}"
        except:
            date_str = "Eintrag"
        
        self.setWindowTitle(f"Tagesgans - {date_str}")
        self.setMinimumSize(900, 700)
        
        # Icon
        icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Hintergrundfarbe setzen
        self.setStyleSheet("QMainWindow { background-color: #f5f5f5; }")
        
        # Hauptlayout
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: #f5f5f5; }")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        
        # Text-Browser für Inhalt
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenLinks(False)
        self.text_browser.anchorClicked.connect(self.on_link_clicked)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                font-size: 14px;
            }
        """)
        
        main_layout.addWidget(self.text_browser, 4)
        
        # Rechte Seitenleiste
        right_panel = QWidget()
        right_panel.setStyleSheet("QWidget { background-color: #f5f5f5; }")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Labels
        label_header = QHBoxLayout()
        label_icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "label.png"
        label_toggle = QToolButton()
        label_toggle.setStyleSheet("QToolButton { background-color: transparent; border: none; }")
        if label_icon_path.exists():
            label_toggle.setIcon(QIcon(str(label_icon_path)))
        label_toggle.setIconSize(QSize(24, 24))
        label_toggle.setCheckable(True)
        label_toggle.setChecked(True)
        label_toggle.toggled.connect(lambda checked: self.label_list.setVisible(checked))
        
        label_title = QLabel("Labels")
        label_title.setStyleSheet("font-weight: bold; font-size: 14px; background-color: transparent;")
        
        label_header.addWidget(label_toggle)
        label_header.addWidget(label_title)
        label_header.addStretch()
        right_layout.addLayout(label_header)
        
        self.label_list = QListWidget()
        self.label_list.itemClicked.connect(self.on_label_clicked)
        self.label_list.setMaximumWidth(200)
        self.label_list.setStyleSheet("""
            QListWidget {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #ffe69c;
            }
        """)
        right_layout.addWidget(self.label_list)
        
        # Zeitstempel
        time_header = QHBoxLayout()
        time_icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "time.png"
        time_toggle = QToolButton()
        time_toggle.setStyleSheet("QToolButton { background-color: transparent; border: none; }")
        if time_icon_path.exists():
            time_toggle.setIcon(QIcon(str(time_icon_path)))
        time_toggle.setIconSize(QSize(24, 24))
        time_toggle.setCheckable(True)
        time_toggle.setChecked(True)
        time_toggle.toggled.connect(lambda checked: self.time_list.setVisible(checked))
        
        time_title = QLabel("Zeitstempel")
        time_title.setStyleSheet("font-weight: bold; font-size: 14px; background-color: transparent;")
        
        time_header.addWidget(time_toggle)
        time_header.addWidget(time_title)
        time_header.addStretch()
        right_layout.addLayout(time_header)
        
        self.time_list = QListWidget()
        self.time_list.itemClicked.connect(self.on_timestamp_clicked)
        self.time_list.setMaximumWidth(200)
        self.time_list.setStyleSheet("""
            QListWidget {
                background-color: #d1ecf1;
                border: 1px solid #0dcaf0;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #bee5eb;
            }
        """)
        right_layout.addWidget(self.time_list)
        
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        
        main_layout.addWidget(right_panel, 1)
        central_widget.setLayout(main_layout)
    
    def load_entry(self):
        """Lädt und zeigt einen Tagebucheintrag"""
        if not self.day_file.exists():
            return
        
        with open(self.day_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.display_content(content, self.day_file.parent)
    
    def display_content(self, content, media_dir):
        """Zeigt formatierten Inhalt an"""
        self.text_browser.clear()
        cursor = self.text_browser.textCursor()
        
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
        self.label_list.clear()
        self.time_list.clear()
        
        for label in self.labels:
            item = QListWidgetItem(f"#{label}")
            self.label_list.addItem(item)
        
        for ts in self.timestamps:
            self.time_list.addItem(ts)
    
    def insert_formatted_line(self, cursor, line, format_info, media_dir):
        """Fügt eine formatierte Zeile ein"""
        size, style, color = format_info
        
        char_format = QTextCharFormat()
        font = QFont()
        font.setPointSize(size)
        font.setBold('F' in style)
        font.setItalic('K' in style)
        font.setUnderline('U' in style)
        font.setStrikeOut('D' in style)
        char_format.setFont(font)
        
        char_format.setForeground(QColor(color))
        
        pos = 0
        while pos < len(line):
            # @Person (vCard)
            person_match = re.match(r'@(\w+)', line[pos:])
            if person_match:
                person_name = person_match.group(1)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("#0066cc"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"person:{person_name}")
                cursor.insertText(f"👤 {person_name}", link_format)
                pos += person_match.end()
                continue
            
            # %Ort (KML)
            place_match = re.match(r'%(\w+)', line[pos:])
            if place_match:
                place_name = place_match.group(1)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("#28a745"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"place:{place_name}")
                cursor.insertText(f"📍 {place_name}", link_format)
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
                cursor.insertText(f"📋 {copy_text}", link_format)
                pos += copy_match.end()
                continue
            
            # §Zeitstempel
            time_match = re.match(r'§([\d.]+)', line[pos:])
            if time_match:
                timestamp = time_match.group(1)
                self.timestamps.append(timestamp)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("#6f42c1"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"time:{timestamp}")
                cursor.insertText(f"🕒 {timestamp}", link_format)
                pos += time_match.end()
                continue
            
            # =Label
            label_match = re.match(r'=(\w+)', line[pos:])
            if label_match:
                label = label_match.group(1)
                if label not in self.labels:
                    self.labels.append(label)
                link_format = QTextCharFormat(char_format)
                link_format.setForeground(QColor("#fd7e14"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(f"label:{label}")
                cursor.insertText(f"🏷️ #{label}", link_format)
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
                link_format.setForeground(QColor("#0066cc"))
                link_format.setFontUnderline(True)
                link_format.setAnchor(True)
                link_format.setAnchorHref(url)
                cursor.insertText(f"🔗 {url}", link_format)
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
            cursor.insertHtml(f'<br><img src="{media_file}" width="500" style="border-radius: 8px;"><br>')
        elif ext in ['.mp3', '.ogg', '.opus', '.mp4']:
            link_format = QTextCharFormat()
            link_format.setForeground(QColor("#0066cc"))
            link_format.setFontUnderline(True)
            link_format.setAnchor(True)
            link_format.setAnchorHref(f"media:{media_file}")
            cursor.insertText(f"\n🎬 [{media_file.name}]\n", link_format)
    
    def on_link_clicked(self, url):
        """Behandelt Klicks auf Links"""
        url_str = url.toString()
        
        if url_str.startswith("person:"):
            person = url_str.split(":", 1)[1]
            vcard_file = self.day_file.parent / f"{person}.vcard"
            if vcard_file.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(vcard_file)))
        
        elif url_str.startswith("place:"):
            place = url_str.split(":", 1)[1]
            kml_file = self.day_file.parent / f"{place}.kml"
            if kml_file.exists():
                os.system(f"qgis '{kml_file}' &")
        
        elif url_str.startswith("copy:"):
            text = url_str.split(":", 1)[1]
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            QMessageBox.information(self, "Kopiert", f"'{text}' wurde kopiert!")
        
        elif url_str.startswith("time:"):
            timestamp = url_str.split(":", 1)[1]
            dialog = CalendarDialog(self, timestamp)
            dialog.exec_()
        
        elif url_str.startswith("label:"):
            pass
        
        elif url_str.startswith("media:"):
            media_path = url_str.split(":", 1)[1]
            QDesktopServices.openUrl(QUrl.fromLocalFile(media_path))
        
        elif url_str.startswith("http"):
            QDesktopServices.openUrl(url)
    
    def on_label_clicked(self, item):
        """Springt zum Label im Text"""
        label = item.text().replace("#", "")
        # Cursor zurücksetzen
        cursor = self.text_browser.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.text_browser.setTextCursor(cursor)
        # Suche nach Label (mit Emoji)
        self.text_browser.find(label)
    
    def on_timestamp_clicked(self, item):
        """Springt zum Zeitstempel im Text"""
        timestamp = item.text()
        # Cursor zurücksetzen
        cursor = self.text_browser.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.text_browser.setTextCursor(cursor)
        # Suche nach Zeitstempel
        self.text_browser.find(timestamp)


class DiaryReader(QMainWindow):
    """Hauptfenster des Tagebuch-Readers"""
    
    def __init__(self, config_file):
        super().__init__()
        self.config_file = Path(config_file)
        self.settings = self.load_settings()
        self.current_diary = None
        self.entry_windows = []
        
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
        self.setMinimumSize(800, 600)
        
        # Icon
        icon_path = Path.home() / ".local" / "share" / "icons" / "Goose" / "tagesgans.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Hintergrundfarbe setzen
        self.setStyleSheet("QMainWindow { background-color: #f0f0f0; }")
        
        # Hauptlayout
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background-color: #f0f0f0; }")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Titel
        title = QLabel("📖 Tagesgans Reader")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: transparent;
            }
        """)
        main_layout.addWidget(title)
        
        # Tagebuch-Auswahl
        diary_label = QLabel("Tagebuch auswählen:" if lang == "Deutsch" else "Select Diary:")
        diary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e; background-color: transparent;")
        main_layout.addWidget(diary_label)
        
        self.diary_list = QListWidget()
        self.diary_list.itemClicked.connect(self.on_diary_selected)
        self.diary_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background-color: #ebf5fb;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        main_layout.addWidget(self.diary_list)
        
        # Eintrags-Navigation als Baum
        entry_label = QLabel("Einträge:" if lang == "Deutsch" else "Entries:")
        entry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34495e; background-color: transparent;")
        main_layout.addWidget(entry_label)
        
        self.entry_tree = QTreeWidget()
        self.entry_tree.setHeaderLabels(["Datum", "Jahr", "Monat"])
        self.entry_tree.itemDoubleClicked.connect(self.on_entry_double_clicked)
        self.entry_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                border: 2px solid #2ecc71;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px;
            }
            QTreeWidget::item:hover {
                background-color: #d5f4e6;
            }
            QTreeWidget::item:selected {
                background-color: #2ecc71;
                color: white;
            }
        """)
        main_layout.addWidget(self.entry_tree)
        
        central_widget.setLayout(main_layout)
    
    def scan_diaries(self):
        """Scannt nach .duckday Ordnern"""
        self.diary_list.clear()
        home = Path.home()
        
        for duckday_dir in home.rglob("*.duckday"):
            if duckday_dir.is_dir():
                diary_name = duckday_dir.stem
                item = QListWidgetItem(f"📔 {diary_name}")
                item.setData(Qt.UserRole, str(duckday_dir))
                
                # Icon laden
                icon_file = duckday_dir / "Icon.png"
                if icon_file.exists():
                    item.setIcon(QIcon(str(icon_file)))
                
                self.diary_list.addItem(item)
    
    def on_diary_selected(self, item):
        """Wird aufgerufen wenn ein Tagebuch ausgewählt wurde"""
        self.current_diary = Path(item.data(Qt.UserRole))
        self.load_entries()
    
    def load_entries(self):
        """Lädt alle Einträge als Baum"""
        self.entry_tree.clear()
        
        if not self.current_diary:
            return
        
        # Jahr → Monat → Tag Hierarchie
        year_items = {}
        
        for year_dir in sorted(self.current_diary.glob("*"), reverse=True):
            if year_dir.is_dir() and year_dir.name.isdigit():
                year_item = QTreeWidgetItem([f"📅 {year_dir.name}"])
                year_item.setExpanded(True)
                self.entry_tree.addTopLevelItem(year_item)
                
                for month_dir in sorted(year_dir.glob("*"), reverse=True):
                    if month_dir.is_dir():
                        month_item = QTreeWidgetItem([f"📆 {month_dir.name}"])
                        month_item.setExpanded(True)
                        year_item.addChild(month_item)
                        
                        for day_dir in sorted(month_dir.glob("*"), reverse=True):
                            if day_dir.is_dir():
                                day_file = day_dir / "Day.txt"
                                if day_file.exists():
                                    day_item = QTreeWidgetItem([f"📝 Tag {day_dir.name}"])
                                    day_item.setData(0, Qt.UserRole, str(day_file))
                                    month_item.addChild(day_item)
    
    def on_entry_double_clicked(self, item, column):
        """Öffnet Eintrag in neuem Fenster"""
        day_file_str = item.data(0, Qt.UserRole)
        if day_file_str:
            day_file = Path(day_file_str)
            window = EntryViewerWindow(day_file, self.settings, self)
            window.show()
            self.entry_windows.append(window)


def main():
    if len(sys.argv) < 2:
        print("Usage: reader.py <config_file>")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DiaryDuck")
    
    # Modernes Theme
    app.setStyle("Fusion")
    
    reader = DiaryReader(sys.argv[1])
    reader.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

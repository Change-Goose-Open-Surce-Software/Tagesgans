#!/bin/bash

mkdir -p ~/.local/bin/tagesgans
mkdir -p ~/.local/share/icons/Goose

wget -O ~/.local/bin/tagesgans/reader.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/reader.py
wget -O ~/.local/bin/tagesgans/tagesgans.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/tagesgans.py
wget -O ~/.local/bin/tagesgans/editor.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/editor.py
wget -O ~/.local/share/icons/Goose/tagesgans.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/icon.py
wget -O ~/.local/share/icons/Goose/time.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Time.png
wget -O ~/.local/share/icons/Goose/label.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Label.png
wget -O ~/.local/share/Applications/tagesgans.desktop https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Tagesgans.desktop

chmod +x ~/.local/bin/reader.py
chmod +x ~/.local/bin/editor.py
chmod +x ~/.local/bin/tagesgans.py
chmod +x ~/.local/share/Applications/tagesgans.desktop

sudo apt update
sudo apt install python3 python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtmultimediawidgets qgis gnome-contacts gnome-calendar xdg-utils gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav -y
sudo update-desktop-database

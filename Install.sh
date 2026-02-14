#!/bin/bash

mkdir -p ~/.local/bin/tagesgans
mkdir -p ~/.local/share/icons/Goose

wget -O ~/.local/bin/tagesgans/reader.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/reader.py
wget -O ~/.local/bin/tagesgans/tagesgans.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/tagesgans.py
wget -O ~/.local/bin/tagesgans/editor.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/editor.py
wget -O ~/.local/share/icons/Goose/tagesgans.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/icon.png
wget -O ~/.local/share/icons/Goose/time.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Time.png
wget -O ~/.local/share/icons/Goose/label.png https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Label.png
wget -O ~/.local/share/applications/tagesgans.desktop https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/Tagesgans.desktop

chmod +x ~/.local/bin/tagesgans/reader.py
chmod +x ~/.local/bin/tagesgans/editor.py
chmod +x ~/.local/bin/tagesgans/tagesgans.py
chmod +x ~/.local/share/applications/tagesgans.desktop

sudo apt update
sudo apt install python3 python3-pyqt5 python3-pyqt5.qtmultimedia qgis gnome-contacts gnome-calendar xdg-utils gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav -y
sudo update-desktop-database

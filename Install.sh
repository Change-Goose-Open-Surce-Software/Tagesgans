#!/bin/bash

mkdir -p ~/.local/bin/tagesgans
mkdir -p ~/.local/share/icons/Goose

wget -O ~/.local/bin/tagesgans/reader.py https://raw.githubusercontent.com/Change-Goose-Open-Surce-Software/Tagesgans/main/reader.py

sudo apt install python3 python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtmultimediawidgets qgis gnome-contacts gnome-calendar xdg-utils gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav -y

#!/bin/bash
# Script Pemasangan EasyScanlate untuk Android/Termux

echo "Memperbarui repositori Termux..."
pkg update && pkg upgrade -y

echo "Menginstal Python dan pustaka dasar C..."
pkg install -y python python-pip libjpeg-turbo libpng

echo "Menginstal mesin OCR (Tesseract) dan paket bahasa Indonesia..."
pkg install -y tesseract tesseract-data-ind tesseract-data-eng

echo "Menginstal modul Python yang dibutuhkan..."
pip install -r requirements.txt

echo ""
echo "========================================="
echo " Instalasi Selesai!"
echo " Anda kini bisa menjalankan tool dengan:"
echo " python termux_scanlate.py <file.cbz>"
echo "========================================="

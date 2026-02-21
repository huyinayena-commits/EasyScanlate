# EasyScanlate (Termux Edition)

EasyScanlate adalah alat praktis untuk mengekstrak teks interaktif (OCR) secara otomatis dari gambar komik/manhwa menjadi format teks (Markdown). 

Versi ini dirancang *sangat ringan* secara khusus untuk berjalan di sistem **Android via Termux** dengan memutar proses bacaan gambar satu per satu untuk mencegah aplikasi tertutup paksa karena kehabisan RAM.

## 🚀 Cara Instalasi di Android

1. **Unduh dan Pasang Aplikasi Termux** 
   Unduh Termux versi terbaru dari F-Droid (jangan dari Google Play Store karena versinya sudah tidak diperbarui).
2. **Berikan Akses Penyimpanan**
   Buka Termux dan ketik perintah berikut, lalu izinkan pop-up yang muncul:
   ```bash
   termux-setup-storage
   ```
3. **Klon / Unduh Skrip Ini**
   Masuk ke Termux dan salin '*folder*' ini ke penyimpanan internal Anda (misalnya: `cd /sdcard/Download`, lalu jalankan git clone atau cukup memindah hasil unduhan .zip ke sana).
   ```bash
   git clone https://github.com/huyinayena-commits/EasyScanlate.git
   cd EasyScanlate
   ```
4. **Jalankan Pemasangan Otomatis**
   Ini hanya perlu dilakukan sekali di awal untuk menginstal Python, Tesseract, Pillow, dsb.
   ```bash
   chmod +x setup_termux.sh
   ./setup_termux.sh
   ```

## 📖 Cara Penggunaan

Simpan komik atau manhwa yang ingin Anda ekstrak teksnya (baik dalam bentuk .cbz/.zip maupun folder gambar) di penyimpanan internal HP Anda, misalnya di folder Download.

Masuk ke folder `EasyScanlate` via Termux, lalu jalankan perintah:

```bash
# Untuk file arsip (.cbz atau .zip)
python termux_scanlate.py /sdcard/Download/komik_chapter1.cbz

# Untuk membaca sebuah judul spesifik dan menghasilkan output Markdown
python termux_scanlate.py /sdcard/Download/komik.cbz -t "Solo Leveling Chapter 1"

# Untuk sebuah folder gambar (kumpulan JPG/PNG)
python termux_scanlate.py /sdcard/Download/folder_gambar_komik
```

File hasil berbentuk `.md` akan secara otomatis muncul di folder direktori asal komik Anda dan siap dibaca di sembarang aplikasi *teks editor*.

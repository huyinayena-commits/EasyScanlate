"""
EasyScanlate - Termux Edition
=============================
Tool berbasis Tesseract OCR dan Pillow yang dirancang ringan
untuk dieksekusi di OS Android (Termux). Pemrosesan gambar 
dilakukan secara sekuensial (satu per satu) untuk mencegah Out-Of-Memory.
"""

import os
import sys
import shutil
import zipfile
import argparse
from pathlib import Path
import re

# Coba import rarfile, jika tidak ada, beri tahu user bahwa rar tidak terdukung di Termux
try:
    import rarfile
except ImportError:
    rarfile = None

from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from natsort import natsorted

# ============================================================================
# Konfigurasi & Setelan
# ============================================================================

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ARCHIVE_EXTENSIONS = {".cbz", ".cbr", ".zip", ".rar"}

WATERMARK_KEYWORDS = [
    "komikindo", "kiryuu", "westmanga", "shinigami", "bacakomik",
    "ngomik", "mangakita", "mangaku", "sektekomik", "boosei",
    "pojokmanga", "mangaid", "komikcast", "maid.my.id", "manhwaid",
    "komik station", "discord.gg", "dukung kami", "traktir kopi"
]

OCR_CHAR_MAP = {
    '1': 'I', '0': 'O', '8': 'B', '5': 'S',
    '@': 'A', '|': 'I', '[': 'I', ']': 'I'
}

# Pola karakter Asia Timur
CJK_PATTERN = re.compile(
    r"[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]"
)

# ============================================================================
# Fungsi Pemrosesan 
# ============================================================================

def preprocess_image(image_path: Path):
    """
    Pra-pemrosesan super ringan dengan Pillow untuk Tesseract.
    Mengubah ke hitam putih dan memperjelas kontras.
    """
    try:
        img = Image.open(image_path)
        # Convert ke grayscale
        img = img.convert('L')
        # Tingkatkan kontras 2x lipat
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        # Median filter untuk membuang bintik-bintik kompresi
        img = img.filter(ImageFilter.MedianFilter(size=3))
        return img
    except Exception as e:
        print(f"Error memproses gambar {image_path.name}: {e}")
        return None

def is_watermark(text: str) -> bool:
    clean_text = text.lower()
    for kw in WATERMARK_KEYWORDS:
        if kw in clean_text:
            return True
    return False

def is_gibberish_or_noise(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 2:
        return True
    
    # Cek rasio huruf alfabet untuk menghindari blok gambar/artefak
    alpha_count = sum(1 for c in stripped if c.isalpha() and ord(c) < 128)
    if len(stripped) > 3 and alpha_count / len(stripped) < 0.4:
        return True
        
    # Cek CJK (jika terlalu banyak kanji/hangul, kemungkinan itu teks aslinya dan bukan terjemahan)
    cjk_count = len(CJK_PATTERN.findall(stripped))
    if cjk_count > 0 and len(stripped) > 0:
        if cjk_count / len(stripped) > 0.3:
            return True

    return False

def fix_ocr_chars(text: str) -> str:
    result = list(text)
    for i, ch in enumerate(result):
        if ch in OCR_CHAR_MAP:
            prev_alpha = (i > 0 and result[i-1].isalpha())
            next_alpha = (i < len(result)-1 and result[i+1].isalpha())
            if prev_alpha or next_alpha:
                result[i] = OCR_CHAR_MAP[ch]
    return "".join(result)

def process_text_block(raw_text: str) -> list:
    """Membersihkan teks dan menyusun teks yang putus karena baris baru."""
    lines = raw_text.split('\n')
    cleaned_dialogs = []
    
    current_sentences = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_sentences:
                cleaned_dialogs.append(" ".join(current_sentences))
                current_sentences = []
            continue
            
        line = fix_ocr_chars(line)
        
        if is_watermark(line) or is_gibberish_or_noise(line):
            continue
            
        current_sentences.append(line)
        
    if current_sentences:
        cleaned_dialogs.append(" ".join(current_sentences))
        
    return cleaned_dialogs

# ============================================================================
# Pipeline Utama Termux
# ============================================================================

def extract_archive(archive_path: Path, temp_dir: Path):
    ext = archive_path.suffix.lower()
    if ext in (".cbz", ".zip"):
        with zipfile.ZipFile(str(archive_path), 'r') as z:
            z.extractall(str(temp_dir))
    elif ext in (".cbr", ".rar"):
        if rarfile is None:
            print("[ERROR] Ekstensi rar (.cbr/.rar) di Termux membutuhkan modul 'rarfile' dan binari 'unrar'.")
            sys.exit(1)
        with rarfile.RarFile(str(archive_path), 'r') as r:
            r.extractall(str(temp_dir))

def process_chapter(input_path: Path, output_md: Path, title: str, lang="ind"):
    is_archive = input_path.is_file()
    temp_dir = input_path.parent / f"_temp_{input_path.stem}"
    
    try:
        if is_archive:
            print(f"[*] Mengekstrak arsip {input_path.name}...")
            temp_dir.mkdir(parents=True, exist_ok=True)
            extract_archive(input_path, temp_dir)
            source_dir = temp_dir
        else:
            source_dir = input_path
            
        images = []
        for root, _, files in os.walk(str(source_dir)):
            for f in files:
                if Path(f).suffix.lower() in IMAGE_EXTENSIONS:
                    images.append(Path(root) / f)
                    
        images = natsorted(images, key=lambda p: p.name)
        
        if not images:
            print("[!] Tidak ada gambar ditemukan dalam input.")
            return
            
        print(f"[*] Menemukan {len(images)} gambar. Memulai memindai OCR...")
        print(f"[*] Perhatian: Ini menggunakan mode antrean satu-satu untuk mencegah Crash di Android.\n")
        
        results = {}
        
        for i, img_path in enumerate(images, start=1):
            print(f"  -> Memproses hal {i}/{len(images)}: {img_path.name}")
            img_processed = preprocess_image(img_path)
            if img_processed is None:
                continue
                
            # Konfigurasi PSM 4: Anggap halaman adalah tabel tunggal penuh teks
            custom_config = r'--oem 3 --psm 4'
            try:
                raw_text = pytesseract.image_to_string(img_processed, lang=lang, config=custom_config)
                clean_dialogs = process_text_block(raw_text)
                results[f"page_{i}"] = clean_dialogs
            except Exception as e:
                print(f"    [!] Error OCR tesseract pada gambar ini: {e}")
                results[f"page_{i}"] = []

        # Tulis Markdown
        with open(str(output_md), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            for key, dialogs in results.items():
                page_num = key.split('_')[1]
                f.write(f"## Halaman {page_num}\n\n")
                if not dialogs:
                    f.write("- *(Tidak ada teks terdeteksi)*\n\n")
                else:
                    for j, txt in enumerate(dialogs, start=1):
                        f.write(f"- **Teks {j}:** {txt}\n")
                f.write("\n")
                
        print(f"\n[v] Berhasil! Hasil transkripsi telah disimpan di:")
        print(f"    {output_md}")

    finally:
        # PENTING: Bersihkan temp agar tidak memenuhi memori internal ponsel
        if is_archive and temp_dir.exists():
            shutil.rmtree(str(temp_dir))

# ============================================================================
# Pemilihan Folder Interaktif (Khusus Termux)
# ============================================================================

def select_kotatsu_folder() -> Path:
    """Menampilkan menu interaktif untuk memilih folder di dalam KOTATSU."""
    kotatsu_dir = Path("/storage/emulated/0/KOTATSU/")
    
    if not kotatsu_dir.exists() or not kotatsu_dir.is_dir():
        print(f"[!] Folder KOTATSU tidak ditemukan di: {kotatsu_dir}")
        print("    Pastikan Anda sudah memberikan izin penyimpanan (termux-setup-storage)")
        sys.exit(1)
        
    print(f"\nMencari komik di: {kotatsu_dir}\n")
    
    # Ambil semua sub-folder
    subfolders = []
    for item in kotatsu_dir.iterdir():
        if item.is_dir():
            subfolders.append(item)
            
    # Urutkan secara alfabetis
    subfolders = sorted(subfolders, key=lambda p: p.name.lower())
    
    if not subfolders:
        print("[!] Tidak ada folder komik di dalam KOTATSU.")
        sys.exit(1)
        
    # Tampilkan opsi
    for i, folder in enumerate(subfolders, start=1):
        print(f"  [{i}] {folder.name}")
        
    print("\n[0] Batal / Keluar")
    
    while True:
        try:
            choice = int(input("\nPilih nomor folder yang ingin diproses: "))
            if choice == 0:
                print("Dibatalkan.")
                sys.exit(0)
            if 1 <= choice <= len(subfolders):
                selected = subfolders[choice - 1]
                print(f"\nAnda memilih: {selected.name}")
                return selected
            else:
                print("Nomor tidak valid. Silakan coba lagi.")
        except ValueError:
            print("Masukkan angka yang valid.")

def process_selected_folder(komik_dir: Path, lang: str):
    """
    Memproses seluruh isi folder komik terpilih.
    Jika ada sub-folder atau .cbz di dalamnya, proses satu per satu.
    Hasil .md disimpan di dalam folder komik tersebut.
    """
    print(f"\n=========================================")
    print(f" Memproses: {komik_dir.name}")
    print(f"=========================================")
    
    # Temukan semua file arsip (.cbz, .zip) di dalam folder utama
    archives = []
    for item in komik_dir.iterdir():
        if item.is_file() and item.suffix.lower() in ARCHIVE_EXTENSIONS:
            archives.append(item)
            
    archives = natsorted(archives, key=lambda p: p.name)
    success_count = 0
    
    if archives:
        print(f"[*] Ditemukan {len(archives)} file arsip (.cbz/.zip)")
        for archive in archives:
            title = f"{komik_dir.name} - {archive.stem}"
            output_md = komik_dir / f"{archive.stem}_transcript.md"
            print(f"\n--- Memproses arsip: {archive.name} ---")
            process_chapter(archive, output_md, title, lang)
            success_count += 1
    else:
        # Jika tidak ada arsip, asumsikan gambar lepas di dalam folder tersebut
        # atau ada sub-folder untuk tiap chapter
        subchapters = [d for d in komik_dir.iterdir() if d.is_dir()]
        subchapters = natsorted(subchapters, key=lambda p: p.name)
        
        if subchapters:
            print(f"[*] Ditemukan {len(subchapters)} sub-folder chapter")
            for sub_dir in subchapters:
                title = f"{komik_dir.name} - {sub_dir.name}"
                output_md = komik_dir / f"{sub_dir.name}_transcript.md"
                print(f"\n--- Memproses chapter: {sub_dir.name} ---")
                process_chapter(sub_dir, output_md, title, lang)
                success_count += 1
        else:
            # Hanya gambar lepas di root folder komik
            title = komik_dir.name
            output_md = komik_dir / f"{komik_dir.name}_transcript.md"
            print(f"\n[*] Memproses gambar lepas di folder utama...")
            process_chapter(komik_dir, output_md, title, lang)
            success_count += 1

    print(f"\n=========================================")
    print(f" Selesai! Semua hasil .md ada di dalam:")
    print(f" {komik_dir}")
    print(f"=========================================")

def main():
    parser = argparse.ArgumentParser(description="EasyScanlate Termux Edition (Tesseract & PIL)")
    parser.add_argument("input", nargs="?", help="Path opsional ke (.cbz) atau Folder gambar. Kosongkan untuk menu interaktif.")
    parser.add_argument("-t", "--title", help="Judul komik (untuk file Hasil MD)", default=None)
    parser.add_argument("-l", "--lang", help="Kode bahasa tesseract (default: ind)", default="ind")
    
    args = parser.parse_args()
    
    if args.input:
        # Mode manual lewat argumen CLI
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print("Path input tidak valid atau tidak ditemukan.")
            sys.exit(1)
            
        title = args.title if args.title else input_path.stem
        output_path = input_path.parent / f"{input_path.stem}_transcript.md"
        process_chapter(input_path, output_path, title, args.lang)
    else:
        # Mode Menu Interaktif KOTATSU
        print("\n=== EasyScanlate - Kotatsu Mode ===")
        selected_folder = select_kotatsu_folder()
        process_selected_folder(selected_folder, args.lang)

if __name__ == "__main__":
    main()

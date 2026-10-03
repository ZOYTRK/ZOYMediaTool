"""Dosya yolu yardımcıları (PyInstaller uyumlu)."""
import os
import sys
import shutil
import subprocess


def resource_path(relative_path: str = "") -> str:
    """PyInstaller ile paketlenmiş veya kaynak koddan çalışırken doğru yolu döndürür."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


APP_NAME = "ZOYMediaTool"
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", APP_NAME)

# Konsol penceresi açılmasın (Windows)
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# Proje klasöründeki ffmpeg.exe / ffprobe.exe PATH'e eklenir
os.environ["PATH"] = resource_path("") + os.pathsep + os.environ.get("PATH", "")


def _first_existing(candidates):
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def find_ffmpeg():
    return _first_existing([resource_path("ffmpeg.exe")]) or shutil.which("ffmpeg")


def find_ffprobe():
    return _first_existing([resource_path("ffprobe.exe")]) or shutil.which("ffprobe")


def find_soffice():
    pf = [os.environ.get("ProgramFiles", r"C:\Program Files"),
          os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]
    return _first_existing([os.path.join(p, "LibreOffice", "program", "soffice.exe") for p in pf]) \
        or shutil.which("soffice")


def find_tesseract():
    pf = [os.environ.get("ProgramFiles", r"C:\Program Files"),
          os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
          os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")]
    return _first_existing([os.path.join(p, "Tesseract-OCR", "tesseract.exe") for p in pf]) \
        or shutil.which("tesseract")


def unique_path(path: str) -> str:
    """Dosya varsa sonuna (1), (2)... ekler."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"

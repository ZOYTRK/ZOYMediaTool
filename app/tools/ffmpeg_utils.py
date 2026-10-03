"""FFmpeg yardımcıları: süre okuma ve ilerleme takipli çalıştırma."""
import json
import os
import re
import subprocess

from ..paths import find_ffmpeg, find_ffprobe, NO_WINDOW


def probe(path):
    exe = find_ffprobe()
    if not exe:
        return {}
    try:
        out = subprocess.run(
            [exe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
            capture_output=True, text=True, creationflags=NO_WINDOW, timeout=60,
        ).stdout
        return json.loads(out or "{}")
    except Exception:
        return {}


def duration_of(path) -> float:
    try:
        return float(probe(path).get("format", {}).get("duration", 0) or 0)
    except Exception:
        return 0.0


def has_audio(path) -> bool:
    return any(s.get("codec_type") == "audio" for s in probe(path).get("streams", []))


def parse_time(text) -> float:
    """'01:02:03.5', '02:03' veya '75' -> saniye"""
    text = (str(text) if text is not None else "").strip()
    if not text:
        return 0.0
    parts = [float(p) for p in text.replace(",", ".").split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def run_ffmpeg(ctx, args, duration=0.0, label="İşleniyor", base=0.0, span=1.0):
    """ffmpeg'i çalıştırır, ilerlemeyi ctx'e bildirir. base/span: toplam ilerleme içindeki dilim."""
    exe = find_ffmpeg()
    if not exe:
        raise RuntimeError("FFmpeg bulunamadı. ffmpeg.exe dosyasını uygulama klasörüne koyun.")
    cmd = [exe, "-hide_banner", "-y", "-nostats", "-progress", "pipe:1", "-loglevel", "error"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    ctx.job["_proc"] = proc
    err_lines = []
    import threading

    def _read_err():
        for line in proc.stderr:
            err_lines.append(line.strip())
    t = threading.Thread(target=_read_err, daemon=True)
    t.start()

    try:
        for line in proc.stdout:
            if ctx.cancelled:
                proc.kill()
                break
            m = re.match(r"out_time_(?:us|ms)=(\d+)", line.strip())
            if m and duration > 0:
                cur = int(m.group(1)) / 1_000_000
                frac = min(cur / duration, 1.0)
                ctx.progress(base + frac * span, f"{label}: %{frac * 100:.0f}")
        proc.wait()
    finally:
        ctx.job.pop("_proc", None)
    t.join(timeout=2)
    ctx.check()
    if proc.returncode != 0:
        msg = next((l for l in reversed(err_lines) if l), "bilinmeyen hata")
        raise RuntimeError(f"FFmpeg: {msg[:300]}")


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]

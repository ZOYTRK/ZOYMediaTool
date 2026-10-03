"""yt-dlp tabanlı indiriciler (YouTube, Instagram, TikTok, X, Facebook ve 1000+ site)."""
import os

import yt_dlp

from ..paths import resource_path


def _size(b):
    if not b:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def _time(s):
    if not s:
        return "00:00"
    m, s = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _collect_paths(info, out):
    if not info:
        return
    for e in info.get("entries") or []:
        _collect_paths(e, out)
    for d in info.get("requested_downloads") or []:
        if d.get("filepath"):
            out.append(d["filepath"])


def download(ctx, urls, options):
    urls = [u.strip() for u in urls if u and u.strip()]
    if not urls:
        raise ValueError("Lütfen en az bir geçerli URL girin.")

    mode = options.get("mode", "video")
    quality = str(options.get("quality", "best"))
    audio_fmt = options.get("audio_format", "mp3")
    bitrate = str(options.get("bitrate", "192"))
    total = len(urls)
    state = {"i": 0}

    def hook(d):
        if ctx.cancelled:
            raise yt_dlp.utils.DownloadCancelled("USER_CANCEL")
        if d["status"] == "downloading":
            done = d.get("downloaded_bytes") or 0
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            frac = done / tot if tot else 0
            overall = (state["i"] + frac * 0.95) / total
            ctx.progress(overall, f"[{state['i'] + 1}/{total}] İndiriliyor %{frac * 100:.1f} | "
                                  f"{_size(done)} / {_size(tot) if tot else '?'} | "
                                  f"{_size(d.get('speed') or 0)}/s | Kalan {_time(d.get('eta'))}")
        elif d["status"] == "finished":
            ctx.progress(None, f"[{state['i'] + 1}/{total}] Dosya işleniyor...")

    opts = {
        "outtmpl": os.path.join(ctx.out_dir, "%(title).150B [%(id)s].%(ext)s"),
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": not options.get("playlist", False),
        "ffmpeg_location": resource_path(""),
        "windowsfilenames": True,
    }

    if mode == "video":
        if quality == "best":
            opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            opts["format"] = (f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
                              f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best")
        opts["merge_output_format"] = options.get("container", "mp4")
    else:
        opts["format"] = "bestaudio/best"
        pp = {"key": "FFmpegExtractAudio", "preferredcodec": audio_fmt}
        if audio_fmt in ("mp3", "m4a", "opus", "aac", "vorbis"):
            pp["preferredquality"] = bitrate
        opts["postprocessors"] = [pp]

    if options.get("subtitles"):
        opts.update({"writesubtitles": True, "subtitleslangs": ["tr", "en"], "writeautomaticsub": False})
    if options.get("thumbnail"):
        opts["writethumbnail"] = True

    for i, url in enumerate(urls):
        state["i"] = i
        ctx.check()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                paths = []
                _collect_paths(info, paths)
                for p in paths:
                    ctx.add_output(p)
        except yt_dlp.utils.DownloadCancelled:
            ctx.check()
            raise
        except Exception as e:
            if ctx.cancelled or "USER_CANCEL" in str(e):
                ctx.check()
            raise RuntimeError(f"{url} indirilemedi: {str(e)[:200]}")

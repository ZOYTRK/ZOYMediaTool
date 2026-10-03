"""Video ve ses araçları (CloudConvert tarzı) — FFmpeg ile."""
from .ffmpeg_utils import run_ffmpeg, duration_of, has_audio, parse_time, probe, stem

# container -> (video codec, audio codec)
VIDEO_DEFAULTS = {
    "mp4": ("libx264", "aac"), "m4v": ("libx264", "aac"), "mov": ("libx264", "aac"),
    "mkv": ("libx264", "aac"), "webm": ("libvpx-vp9", "libopus"), "avi": ("mpeg4", "libmp3lame"),
    "flv": ("libx264", "aac"), "wmv": ("wmv2", "wmav2"), "mpeg": ("mpeg2video", "mp2"),
    "mpg": ("mpeg2video", "mp2"), "3gp": ("libx264", "aac"), "ts": ("libx264", "aac"),
    "ogv": ("libtheora", "libvorbis"), "mts": ("libx264", "ac3"),
}
VCODEC_CHOICES = {"h264": "libx264", "h265": "libx265", "vp9": "libvpx-vp9", "av1": "libaom-av1"}

# format -> (codec, extension, bitrate destekli mi)
AUDIO_DEFAULTS = {
    "mp3": ("libmp3lame", "mp3", True), "wav": ("pcm_s16le", "wav", False),
    "flac": ("flac", "flac", False), "aac": ("aac", "aac", True), "m4a": ("aac", "m4a", True),
    "ogg": ("libvorbis", "ogg", True), "opus": ("libopus", "opus", True), "wma": ("wmav2", "wma", True),
    "aiff": ("pcm_s16be", "aiff", False), "ac3": ("ac3", "ac3", True), "amr": ("libopencore_amrnb", "amr", False),
}


def _quality_args(vcodec, crf):
    crf = int(crf)
    if vcodec in ("libx264", "libx265"):
        return ["-crf", str(crf), "-preset", "medium"]
    if vcodec == "libvpx-vp9":
        return ["-crf", str(min(crf + 10, 63)), "-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4"]
    if vcodec == "libaom-av1":
        return ["-crf", str(min(crf + 10, 63)), "-b:v", "0", "-cpu-used", "8", "-row-mt", "1"]
    if vcodec in ("mpeg4", "mpeg2video", "wmv2"):
        q = max(2, min(31, int((crf - 14) / 1.5)))
        return ["-q:v", str(q)]
    if vcodec == "libtheora":
        return ["-q:v", str(max(0, min(10, 10 - (crf - 18) // 2)))]
    return []


def _vfilters(opts):
    vf = []
    h = str(opts.get("resolution", "orig"))
    if h != "orig":
        vf.append(f"scale=-2:'min({h},ih)'")
    fps = str(opts.get("fps", "orig"))
    if fps != "orig":
        vf.append(f"fps={fps}")
    return vf


def video_convert(ctx, files, opts):
    fmt = opts.get("format", "mp4")
    for i, f in enumerate(files):
        vdef, adef = VIDEO_DEFAULTS.get(fmt, ("libx264", "aac"))
        choice = opts.get("vcodec", "auto")
        vcodec = VCODEC_CHOICES.get(choice, vdef)
        out = ctx.out_path(f"{stem(f)}.{fmt}")
        args = ["-i", f]
        if choice == "copy":
            args += ["-c", "copy"]
        else:
            vf = _vfilters(opts)
            if vcodec in ("libx264", "libx265"):
                vf.append("format=yuv420p")
            if vf:
                args += ["-vf", ",".join(vf)]
            args += ["-c:v", vcodec] + _quality_args(vcodec, opts.get("crf", 23))
            if opts.get("mute"):
                args += ["-an"]
            else:
                args += ["-c:a", adef, "-b:a", "192k"]
            if fmt in ("mp4", "m4v", "mov"):
                args += ["-movflags", "+faststart"]
            if fmt == "3gp":
                args += ["-ar", "44100"]
        args.append(out)
        run_ffmpeg(ctx, args, duration_of(f), f"[{i + 1}/{len(files)}] Dönüştürülüyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def audio_convert(ctx, files, opts):
    fmt = opts.get("format", "mp3")
    codec, ext, br_ok = AUDIO_DEFAULTS.get(fmt, AUDIO_DEFAULTS["mp3"])
    for i, f in enumerate(files):
        out = ctx.out_path(f"{stem(f)}.{ext}")
        args = ["-i", f, "-vn", "-map", "0:a:0?", "-c:a", codec]
        if br_ok:
            args += ["-b:a", f"{opts.get('bitrate', '192')}k"]
        sr = str(opts.get("samplerate", "orig"))
        if sr != "orig":
            args += ["-ar", sr]
        elif fmt == "opus":
            args += ["-ar", "48000"]
        ch = str(opts.get("channels", "orig"))
        if ch != "orig":
            args += ["-ac", ch]
        if fmt == "amr":
            args += ["-ar", "8000", "-ac", "1", "-b:a", "12.2k"]
        args.append(out)
        run_ffmpeg(ctx, args, duration_of(f), f"[{i + 1}/{len(files)}] Ses dönüştürülüyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def video_compress(ctx, files, opts):
    level = opts.get("level", "medium")
    for i, f in enumerate(files):
        dur = duration_of(f)
        out = ctx.out_path(f"{stem(f)}_sikistirilmis.mp4")
        vf = _vfilters(opts) + ["format=yuv420p"]
        args = ["-i", f, "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium"]
        if level == "size":
            target_mb = float(opts.get("target_mb", 25))
            audio_k = 96
            v_k = max(100, int(target_mb * 8192 / max(dur, 1) - audio_k))
            args += ["-b:v", f"{v_k}k", "-maxrate", f"{int(v_k * 1.2)}k", "-bufsize", f"{v_k * 2}k"]
        else:
            args += ["-crf", {"light": "24", "medium": "28", "strong": "33"}[level]]
            audio_k = 128 if level != "strong" else 96
        args += ["-c:a", "aac", "-b:a", f"{audio_k}k", "-movflags", "+faststart", out]
        run_ffmpeg(ctx, args, dur, f"[{i + 1}/{len(files)}] Sıkıştırılıyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def media_trim(ctx, files, opts):
    start = parse_time(opts.get("start", "0"))
    end = parse_time(opts.get("end", ""))
    for i, f in enumerate(files):
        dur = duration_of(f)
        stop = end if end > start else dur
        ext = f.rsplit(".", 1)[-1].lower() if "." in f else "mp4"
        out = ctx.out_path(f"{stem(f)}_kesit.{ext}")
        args = ["-ss", f"{start}", "-i", f, "-t", f"{max(stop - start, 0.1)}"]
        if opts.get("precise", True):
            args += ["-map", "0:v?", "-map", "0:a?"]
            if any(s.get("codec_type") == "video" for s in probe(f).get("streams", [])):
                args += ["-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p"]
            if ext in ("mp4", "mov", "m4v", "m4a", "mkv"):
                args += ["-c:a", "aac"]
        else:
            args += ["-c", "copy"]
        args.append(out)
        run_ffmpeg(ctx, args, stop - start, f"[{i + 1}/{len(files)}] Kesiliyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def video_merge(ctx, files, opts):
    if len(files) < 2:
        raise ValueError("Birleştirmek için en az 2 video seçin.")
    h = int(opts.get("height", 720))
    w = int(round(h * 16 / 9 / 2) * 2)
    args, filters, concat_in = [], [], ""
    total = 0.0
    extra = len(files)
    for f in files:
        args += ["-i", f]
    for idx, f in enumerate(files):
        d = duration_of(f)
        total += d
        filters.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                       f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{idx}]")
        if has_audio(f):
            filters.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo[a{idx}]")
            concat_in += f"[v{idx}][a{idx}]"
        else:
            args += ["-f", "lavfi", "-t", f"{d or 1}", "-i", "anullsrc=r=44100:cl=stereo"]
            concat_in += f"[v{idx}][{extra}:a]"
            extra += 1
    filters.append(f"{concat_in}concat=n={len(files)}:v=1:a=1[v][a]")
    out = ctx.out_path(f"birlestirilmis_{stem(files[0])}.mp4")
    args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", out]
    run_ffmpeg(ctx, args, total, "Birleştiriliyor")
    ctx.add_output(out)


def audio_merge(ctx, files, opts):
    if len(files) < 2:
        raise ValueError("Birleştirmek için en az 2 ses dosyası seçin.")
    fmt = opts.get("format", "mp3")
    codec, ext, br_ok = AUDIO_DEFAULTS.get(fmt, AUDIO_DEFAULTS["mp3"])
    args, chain = [], ""
    for f in files:
        args += ["-i", f]
    filters = [f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]" for i in range(len(files))]
    chain = "".join(f"[a{i}]" for i in range(len(files)))
    filters.append(f"{chain}concat=n={len(files)}:v=0:a=1[out]")
    out = ctx.out_path(f"birlestirilmis_{stem(files[0])}.{ext}")
    args += ["-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", codec]
    if br_ok:
        args += ["-b:a", "192k"]
    args.append(out)
    run_ffmpeg(ctx, args, sum(duration_of(f) for f in files), "Birleştiriliyor")
    ctx.add_output(out)


def video_to_gif(ctx, files, opts):
    fps = int(opts.get("fps", 12))
    width = int(opts.get("width", 480))
    start = parse_time(opts.get("start", "0"))
    length = parse_time(opts.get("length", "5"))
    for i, f in enumerate(files):
        out = ctx.out_path(f"{stem(f)}.gif")
        vf = (f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];"
              f"[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5")
        args = ["-ss", str(start)]
        if length > 0:
            args += ["-t", str(length)]
        args += ["-i", f, "-filter_complex", vf, "-loop", "0", out]
        run_ffmpeg(ctx, args, length or duration_of(f), f"[{i + 1}/{len(files)}] GIF oluşturuluyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def video_mute(ctx, files, opts):
    for i, f in enumerate(files):
        ext = f.rsplit(".", 1)[-1]
        out = ctx.out_path(f"{stem(f)}_sessiz.{ext}")
        run_ffmpeg(ctx, ["-i", f, "-c:v", "copy", "-an", out], duration_of(f),
                   f"[{i + 1}/{len(files)}] Ses kaldırılıyor", base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def video_rotate(ctx, files, opts):
    vf = {"90": "transpose=1", "270": "transpose=2", "180": "transpose=1,transpose=1",
          "hflip": "hflip", "vflip": "vflip"}[str(opts.get("rotation", "90"))]
    for i, f in enumerate(files):
        out = ctx.out_path(f"{stem(f)}_dondurulmus.mp4")
        run_ffmpeg(ctx, ["-i", f, "-vf", vf + ",format=yuv420p", "-c:v", "libx264", "-crf", "20",
                         "-preset", "medium", "-c:a", "copy", out],
                   duration_of(f), f"[{i + 1}/{len(files)}] Döndürülüyor", base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def audio_volume(ctx, files, opts):
    mode = opts.get("mode", "normalize")
    for i, f in enumerate(files):
        ext = f.rsplit(".", 1)[-1].lower()
        out = ctx.out_path(f"{stem(f)}_ses.{ext}")
        af = "loudnorm=I=-16:TP=-1.5:LRA=11" if mode == "normalize" else f"volume={opts.get('db', 3)}dB"
        args = ["-i", f, "-af", af]
        if any(s.get("codec_type") == "video" for s in probe(f).get("streams", [])):
            args += ["-c:v", "copy"]
        args.append(out)
        run_ffmpeg(ctx, args, duration_of(f), f"[{i + 1}/{len(files)}] Ses ayarlanıyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)


def video_speed(ctx, files, opts):
    speed = float(opts.get("speed", 2))
    atempo = []
    s = speed
    while s > 2.0:
        atempo.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        atempo.append("atempo=0.5")
        s /= 0.5
    atempo.append(f"atempo={s:.4f}")
    for i, f in enumerate(files):
        out = ctx.out_path(f"{stem(f)}_{speed:g}x.mp4")
        args = ["-i", f, "-vf", f"setpts={1 / speed:.5f}*PTS,format=yuv420p", "-c:v", "libx264", "-crf", "21"]
        if has_audio(f):
            args += ["-af", ",".join(atempo), "-c:a", "aac"]
        else:
            args += ["-an"]
        args.append(out)
        run_ffmpeg(ctx, args, duration_of(f) / speed, f"[{i + 1}/{len(files)}] Hız değiştiriliyor",
                   base=i / len(files), span=1 / len(files))
        ctx.add_output(out)

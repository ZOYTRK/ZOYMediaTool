"""Görsel araçları (Pillow): dönüştür, sıkıştır, yeniden boyutlandır, döndür."""
import os

from PIL import Image, ImageOps

try:  # iPhone HEIC desteği (opsiyonel: pip install pillow-heif)
    from pillow_heif import register_heif_opener
    register_heif_opener()
except Exception:
    pass

from .ffmpeg_utils import stem

PIL_FORMAT = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "bmp": "BMP", "gif": "GIF",
              "tiff": "TIFF", "ico": "ICO", "pdf": "PDF", "avif": "AVIF", "tga": "TGA", "ppm": "PPM"}
NO_ALPHA = {"JPEG", "BMP", "PDF", "PPM"}


def _flatten(img, fmt):
    if fmt in NO_ALPHA:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            return bg
        return img.convert("RGB")
    if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
        img = img.convert("RGBA")
    return img


def _save(img, path, fmt, quality=90, src=None):
    kw = {}
    if fmt in ("JPEG", "WEBP", "AVIF"):
        kw["quality"] = int(quality)
    if fmt == "JPEG":
        kw.update(optimize=True, progressive=True)
    if fmt == "PNG":
        kw["optimize"] = True
    if fmt == "ICO":
        kw["sizes"] = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256) if s <= max(img.size)] or [(16, 16)]
    if fmt == "PDF":
        kw["resolution"] = 150
    if src is not None and getattr(src, "n_frames", 1) > 1 and fmt in ("GIF", "WEBP"):
        frames = []
        for i in range(src.n_frames):
            src.seek(i)
            frames.append(src.convert("RGBA"))
        frames[0].save(path, fmt, save_all=True, append_images=frames[1:], loop=0,
                       duration=src.info.get("duration", 100), **kw)
        return
    img.save(path, fmt, **kw)


def _open(path):
    img = Image.open(path)
    return img, ImageOps.exif_transpose(img.copy()) if getattr(img, "n_frames", 1) == 1 else img


def image_convert(ctx, files, opts):
    ext = opts.get("format", "png")
    fmt = PIL_FORMAT[ext]
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"[{i + 1}/{len(files)}] {os.path.basename(f)}")
        src, img = _open(f)
        out = ctx.out_path(f"{stem(f)}.{ext}")
        _save(_flatten(img, fmt), out, fmt, opts.get("quality", 90), src)
        ctx.add_output(out)


def image_compress(ctx, files, opts):
    q = int(opts.get("quality", 70))
    max_side = int(opts.get("max_side", 0) or 0)
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"[{i + 1}/{len(files)}] Sıkıştırılıyor: {os.path.basename(f)}")
        src, img = _open(f)
        ext = os.path.splitext(f)[1].lower().lstrip(".")
        ext = "jpg" if ext in ("jpeg", "jfif") else ext
        if ext not in PIL_FORMAT or ext in ("ico", "pdf"):
            ext = "jpg"
        fmt = PIL_FORMAT[ext]
        if max_side and max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.LANCZOS)
        img = _flatten(img, fmt)
        if fmt == "PNG" and q < 90:
            img = img.convert("RGBA").quantize(colors=max(16, int(256 * q / 100)), method=Image.FASTOCTREE)
        out = ctx.out_path(f"{stem(f)}_sikistirilmis.{ext}")
        _save(img, out, fmt, q)
        ctx.add_output(out)


def image_resize(ctx, files, opts):
    mode = opts.get("mode", "percent")
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"[{i + 1}/{len(files)}] Boyutlandırılıyor")
        src, img = _open(f)
        w, h = img.size
        if mode == "percent":
            p = float(opts.get("percent", 50)) / 100
            size = (max(1, int(w * p)), max(1, int(h * p)))
        elif mode == "width":
            nw = int(opts.get("width", 1280))
            size = (nw, max(1, int(h * nw / w)))
        elif mode == "height":
            nh = int(opts.get("height", 720))
            size = (max(1, int(w * nh / h)), nh)
        else:
            size = (int(opts.get("width", 1280)), int(opts.get("height", 720)))
        img = img.resize(size, Image.LANCZOS)
        ext = os.path.splitext(f)[1].lower().lstrip(".") or "png"
        ext = "jpg" if ext in ("jpeg", "jfif") else ext
        fmt = PIL_FORMAT.get(ext, "PNG")
        out = ctx.out_path(f"{stem(f)}_{size[0]}x{size[1]}.{ext if ext in PIL_FORMAT else 'png'}")
        _save(_flatten(img, fmt), out, fmt, 92)
        ctx.add_output(out)


def image_rotate(ctx, files, opts):
    op = str(opts.get("rotation", "90"))
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"[{i + 1}/{len(files)}] Döndürülüyor")
        src, img = _open(f)
        if op == "hflip":
            img = ImageOps.mirror(img)
        elif op == "vflip":
            img = ImageOps.flip(img)
        else:
            img = img.rotate(-int(op), expand=True)
        ext = os.path.splitext(f)[1].lower().lstrip(".")
        ext = "jpg" if ext in ("jpeg", "jfif") else ext
        fmt = PIL_FORMAT.get(ext, "PNG")
        out = ctx.out_path(f"{stem(f)}_dondurulmus.{ext if ext in PIL_FORMAT else 'png'}")
        _save(_flatten(img, fmt), out, fmt, 92)
        ctx.add_output(out)

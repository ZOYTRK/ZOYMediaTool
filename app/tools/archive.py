"""Arşiv araçları: ZIP / TAR oluşturma ve çıkarma."""
import os
import tarfile
import zipfile

from .ffmpeg_utils import stem

TAR_MODES = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2", "tar.xz": "w:xz"}


def archive_create(ctx, files, opts):
    fmt = opts.get("format", "zip")
    name = (opts.get("name") or "").strip() or (stem(files[0]) if len(files) == 1 else "arsiv")
    out = ctx.out_path(f"{name}.{fmt}")
    if fmt == "zip":
        level = int(opts.get("level", 6))
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=level) as z:
            for i, f in enumerate(files):
                ctx.progress(i / len(files), f"Ekleniyor: {os.path.basename(f)}")
                z.write(f, os.path.basename(f))
    else:
        with tarfile.open(out, TAR_MODES[fmt]) as t:
            for i, f in enumerate(files):
                ctx.progress(i / len(files), f"Ekleniyor: {os.path.basename(f)}")
                t.add(f, os.path.basename(f))
    ctx.add_output(out)


def _safe_target(base, member):
    target = os.path.realpath(os.path.join(base, member))
    if not target.startswith(os.path.realpath(base)):
        raise ValueError(f"Güvensiz arşiv yolu: {member}")
    return target


def archive_extract(ctx, files, opts):
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Çıkarılıyor: {os.path.basename(f)}")
        dest = ctx.out_path(stem(f).replace(".tar", ""))
        os.makedirs(dest, exist_ok=True)
        low = f.lower()
        if zipfile.is_zipfile(f):
            with zipfile.ZipFile(f) as z:
                for m in z.namelist():
                    _safe_target(dest, m)
                z.extractall(dest)
        elif tarfile.is_tarfile(f):
            with tarfile.open(f) as t:
                t.extractall(dest, filter="data")
        elif low.endswith(".7z"):
            try:
                import py7zr
            except ImportError:
                raise RuntimeError("7z için: pip install py7zr")
            with py7zr.SevenZipFile(f) as z:
                z.extractall(dest)
        elif low.endswith(".gz"):
            import gzip
            import shutil
            with gzip.open(f, "rb") as src, open(os.path.join(dest, stem(f)), "wb") as dst:
                shutil.copyfileobj(src, dst)
        else:
            raise RuntimeError(f"Desteklenmeyen arşiv: {os.path.basename(f)}")
        ctx.add_output(dest)

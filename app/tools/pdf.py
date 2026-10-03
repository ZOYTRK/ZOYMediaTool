"""iLovePDF tarzı tüm PDF araçları (PyMuPDF / fitz, pypdf ve Pillow ile)."""
import os
import io
import pymupdf as fitz
from PIL import Image
from pypdf import PdfReader, PdfWriter
from .ffmpeg_utils import stem
from ..paths import find_soffice, find_tesseract, NO_WINDOW
import subprocess

def pdf_merge(ctx, files, opts):
    if len(files) < 2:
        raise ValueError("Birleştirmek için en az 2 PDF dosyası seçin.")
    doc = fitz.open()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Ekleniyor: {os.path.basename(f)}")
        sub = fitz.open(f)
        doc.insert_pdf(sub)
        sub.close()
    out = ctx.out_path(f"birlestirilmis_{stem(files[0])}.pdf")
    doc.save(out)
    doc.close()
    ctx.add_output(out)

def pdf_split(ctx, files, opts):
    ranges_str = opts.get("ranges", "").strip()
    for idx, f in enumerate(files):
        ctx.progress(idx / len(files), f"Bölünüyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        total = len(doc)
        if not ranges_str:
            for page_num in range(total):
                single = fitz.open()
                single.insert_pdf(doc, from_page=page_num, to_page=page_num)
                out = ctx.out_path(f"{stem(f)}_sayfa_{page_num + 1}.pdf")
                single.save(out)
                single.close()
                ctx.add_output(out)
        else:
            chunks = [r.strip() for r in ranges_str.split(",") if r.strip()]
            for c_idx, chunk in enumerate(chunks):
                if "-" in chunk:
                    sp, ep = chunk.split("-", 1)
                    sp = max(1, int(sp.strip())) - 1
                    ep = min(total, int(ep.strip())) - 1
                else:
                    sp = ep = max(1, min(total, int(chunk))) - 1
                if sp <= ep:
                    part = fitz.open()
                    part.insert_pdf(doc, from_page=sp, to_page=ep)
                    out = ctx.out_path(f"{stem(f)}_aralik_{sp+1}-{ep+1}.pdf")
                    part.save(out)
                    part.close()
                    ctx.add_output(out)
        doc.close()

def pdf_remove(ctx, files, opts):
    pages_to_remove = set()
    raw = str(opts.get("pages", "")).split(",")
    for p in raw:
        p = p.strip()
        if p.isdigit():
            pages_to_remove.add(int(p) - 1)
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Sayfalar çıkarılıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        keep = [p for p in range(len(doc)) if p not in pages_to_remove]
        if not keep:
            raise ValueError("Tüm sayfaları silemezsiniz.")
        doc.select(keep)
        out = ctx.out_path(f"{stem(f)}_duzenlenmis.pdf")
        doc.save(out)
        doc.close()
        ctx.add_output(out)

def pdf_compress(ctx, files, opts):
    level = opts.get("level", "medium")
    # medium: deflate + garbage 4, high: render downsample
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Sıkıştırılıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        out = ctx.out_path(f"{stem(f)}_sikistirilmis.pdf")
        if level == "extreme":
            doc.save(out, garbage=4, deflate=True, clean=True, deflate_images=True, deflate_fonts=True)
        else:
            doc.save(out, garbage=3, deflate=True, clean=True)
        doc.close()
        ctx.add_output(out)

def pdf_repair(ctx, files, opts):
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Onarılıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        out = ctx.out_path(f"{stem(f)}_onarilmis.pdf")
        doc.save(out, garbage=4, clean=True, linear=True)
        doc.close()
        ctx.add_output(out)

def jpg_to_pdf(ctx, files, opts):
    doc = fitz.open()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Ekleniyor: {os.path.basename(f)}")
        img = Image.open(f)
        img_bytes = io.BytesIO()
        img.convert("RGB").save(img_bytes, format="PDF")
        img_pdf = fitz.open("pdf", img_bytes.getvalue())
        doc.insert_pdf(img_pdf)
        img_pdf.close()
    out = ctx.out_path(f"gorseller_{stem(files[0])}.pdf")
    doc.save(out)
    doc.close()
    ctx.add_output(out)

def pdf_to_jpg(ctx, files, opts):
    dpi = int(opts.get("dpi", 150))
    fmt = opts.get("format", "jpg").lower()
    for i, f in enumerate(files):
        doc = fitz.open(f)
        total = len(doc)
        for p_idx in range(total):
            ctx.progress((i + p_idx / total) / len(files), f"Dönüştürülüyor sayfa {p_idx + 1}/{total}")
            page = doc[p_idx]
            pix = page.get_pixmap(dpi=dpi)
            out = ctx.out_path(f"{stem(f)}_sayfa_{p_idx + 1}.{fmt}")
            pix.save(out)
            ctx.add_output(out)
        doc.close()

def pdf_rotate(ctx, files, opts):
    angle = int(opts.get("angle", 90))
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Döndürülüyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        for page in doc:
            page.set_rotation((page.rotation + angle) % 360)
        out = ctx.out_path(f"{stem(f)}_dondurulmus.pdf")
        doc.save(out)
        doc.close()
        ctx.add_output(out)

def pdf_watermark(ctx, files, opts):
    text = opts.get("text", "GİZLİ / CONFIDENTIAL")
    opacity = float(opts.get("opacity", 0.3))
    font_size = int(opts.get("size", 36))
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Filigran ekleniyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        for page in doc:
            rect = page.rect
            p = fitz.Point(rect.width / 4, rect.height / 2)
            page.insert_text(p, text, fontsize=font_size, rotate=45, color=(0.7, 0.7, 0.7), fill_opacity=opacity)
        out = ctx.out_path(f"{stem(f)}_filigranli.pdf")
        doc.save(out)
        doc.close()
        ctx.add_output(out)

def pdf_numbers(ctx, files, opts):
    pos = opts.get("position", "bottom-right")
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Numaralandırılıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        total = len(doc)
        for idx, page in enumerate(doc):
            rect = page.rect
            text = f"{idx + 1} / {total}"
            if pos == "bottom-right":
                p = fitz.Point(rect.width - 70, rect.height - 25)
            elif pos == "bottom-center":
                p = fitz.Point(rect.width / 2 - 20, rect.height - 25)
            else:
                p = fitz.Point(35, rect.height - 25)
            page.insert_text(p, text, fontsize=10, color=(0.2, 0.2, 0.2))
        out = ctx.out_path(f"{stem(f)}_numarali.pdf")
        doc.save(out)
        doc.close()
        ctx.add_output(out)

def pdf_protect(ctx, files, opts):
    password = opts.get("password", "")
    if not password:
        raise ValueError("Lütfen bir şifre belirleyin.")
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Şifreleniyor: {os.path.basename(f)}")
        reader = PdfReader(f)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(user_password=password, owner_password=password)
        out = ctx.out_path(f"{stem(f)}_sifreli.pdf")
        with open(out, "wb") as out_file:
            writer.write(out_file)
        ctx.add_output(out)

def pdf_unlock(ctx, files, opts):
    password = opts.get("password", "")
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Şifre çözülüyor: {os.path.basename(f)}")
        reader = PdfReader(f)
        if reader.is_encrypted:
            reader.decrypt(password)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = ctx.out_path(f"{stem(f)}_kilitsiz.pdf")
        with open(out, "wb") as out_file:
            writer.write(out_file)
        ctx.add_output(out)

def pdf_to_word(ctx, files, opts):
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx kurulu değil.")
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Word'e aktarılıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        word_doc = Document()
        for page in doc:
            text = page.get_text()
            word_doc.add_paragraph(text)
            word_doc.add_page_break()
        doc.close()
        out = ctx.out_path(f"{stem(f)}.docx")
        word_doc.save(out)
        ctx.add_output(out)

def _docx_to_pdf_fallback(docx_path, pdf_path):
    from docx import Document
    doc = Document(docx_path)
    pdf = fitz.open()
    page = pdf.new_page(width=595, height=842)
    y = 50
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            y += 14
            continue
        rect = fitz.Rect(50, y, 545, y + 80)
        page.insert_textbox(rect, txt, fontsize=11, fontname="helv")
        y += 18 + txt.count('\n') * 14
        if y > 780:
            page = pdf.new_page(width=595, height=842)
            y = 50
    for table in doc.tables:
        for row in table.rows:
            row_txt = "  |  ".join(cell.text.strip() for cell in row.cells)
            if row_txt:
                rect = fitz.Rect(50, y, 545, y + 30)
                page.insert_textbox(rect, row_txt, fontsize=10, fontname="helv")
                y += 20
                if y > 780:
                    page = pdf.new_page(width=595, height=842)
                    y = 50
    pdf.save(pdf_path)
    pdf.close()

def office_to_pdf(ctx, files, opts):
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"PDF'e dönüştürülüyor: {os.path.basename(f)}")
        out = ctx.out_path(f"{stem(f)}.pdf")
        ext = os.path.splitext(f)[1].lower()
        if ext in (".doc", ".docx"):
            converted = False
            # 1. Öncelik: MS Word varsa %100 orijinal kalitede çevir
            try:
                from docx2pdf import convert
                convert(f, out)
                converted = os.path.exists(out) and os.path.getsize(out) > 0
            except Exception:
                converted = False
            # 2. Öncelik: Kullanıcıda Office yoksa saf Python ile kurulumsuz çevir
            if not converted:
                _docx_to_pdf_fallback(f, out)
            ctx.add_output(out)
        else:
            soffice = find_soffice()
            if soffice:
                cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", ctx.out_dir, f]
                subprocess.run(cmd, check=True, creationflags=NO_WINDOW)
                ctx.add_output(out)
            else:
                raise RuntimeError(f"{ext} için dosya okuyucu bulunamadı.")

def pdf_ocr(ctx, files, opts):
    from rapidocr_onnxruntime import RapidOCR
    import numpy as np
    engine = RapidOCR()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"OCR taranıyor: {os.path.basename(f)}")
        doc = fitz.open(f)
        out_doc = fitz.open()
        for p_idx, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
            ocr_result, _ = engine(img_np)
            new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=pix.tobytes("png"))
            if ocr_result:
                scale_x = page.rect.width / pix.w
                scale_y = page.rect.height / pix.h
                for item in ocr_result:
                    box, text, score = item
                    p1 = fitz.Point(box[0][0] * scale_x, box[0][1] * scale_y)
                    # render_mode 3 = invisible text (searchable PDF overlay)
                    new_page.insert_text(p1, text, fontsize=9, color=(0, 0, 0), render_mode=3)
        out = ctx.out_path(f"{stem(f)}_ocr.pdf")
        out_doc.save(out)
        out_doc.close()
        doc.close()
        ctx.add_output(out)


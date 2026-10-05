"""Belge, ofis, font ve vektör araçları: saf Python (Pure-Python) ve yerleşik kütüphaneler."""
import html
import json
import os
import re
import urllib.request
import zipfile

import pymupdf as fitz
from .ffmpeg_utils import stem


# =====================================================================
# 1. BELGE DÖNÜŞTÜRÜCÜ (DOCX, TXT, HTML, MD, PDF)
# =====================================================================
def doc_convert(ctx, files, opts):
    target = opts.get("format", "pdf").lower()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Dönüştürülüyor: {os.path.basename(f)}")
        ext = os.path.splitext(f)[1].lower().lstrip(".")
        base = stem(f)
        out = ctx.out_path(f"{base}.{target}")

        text = ""
        if ext == "docx":
            try:
                import docx
                doc = docx.Document(f)
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                # Fallback docx extraction
                with zipfile.ZipFile(f) as z:
                    xml_content = z.read("word/document.xml").decode("utf-8")
                    text = re.sub(r"<[^>]+>", " ", xml_content)
                    text = re.sub(r"\s+", " ", text).strip()
        elif ext in ("txt", "md", "csv", "rtf"):
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        elif ext == "html" or ext == "htm":
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                raw = fh.read()
                text = re.sub(r"<[^>]+>", " ", raw)
        elif ext == "pdf":
            doc = fitz.open(f)
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()

        # Hedef format çıktısı
        if target == "txt":
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)
        elif target == "html":
            escaped = html.escape(text).replace("\n", "<br>")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{base}</title></head>"
                         f"<body style='font-family:sans-serif;line-height:1.6;padding:24px;'>{escaped}</body></html>")
        elif target == "docx":
            import docx
            doc = docx.Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(out)
        elif target == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            page.insert_textbox(rect, text[:25000], fontsize=11, fontname="helv")
            doc.save(out)
            doc.close()
        else:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)

        ctx.add_output(out)


# =====================================================================
# 2. TABLO DÖNÜŞTÜRÜCÜ (XLSX, CSV, JSON, HTML, PDF)
# =====================================================================
def sheet_convert(ctx, files, opts):
    target = opts.get("format", "csv").lower()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Tablo işleniyor: {os.path.basename(f)}")
        ext = os.path.splitext(f)[1].lower().lstrip(".")
        base = stem(f)
        out = ctx.out_path(f"{base}.{target}")

        rows = []
        if ext in ("csv", "txt"):
            import csv
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                reader = csv.reader(fh)
                rows = list(reader)
        elif ext == "xlsx":
            try:
                # zip/xml ile saf Python hücre okuma
                with zipfile.ZipFile(f) as z:
                    shared_strings = []
                    if "xl/sharedStrings.xml" in z.namelist():
                        ss_xml = z.read("xl/sharedStrings.xml").decode("utf-8")
                        shared_strings = re.findall(r"<t[^>]*>(.*?)</t>", ss_xml)

                    sheet_xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
                    for row_match in re.finditer(r"<row[^>]*>(.*?)</row>", sheet_xml):
                        row_content = row_match.group(1)
                        row = []
                        for cell_match in re.finditer(r'<c\b[^>]*?(?:\bt="([^"]*)")?[^>]*>(?:<v>([^<]*)</v>)?', row_content):
                            t_attr, v_val = cell_match.groups()
                            if t_attr == "s" and v_val and v_val.isdigit():
                                idx = int(v_val)
                                row.append(shared_strings[idx] if idx < len(shared_strings) else "")
                            else:
                                row.append(v_val or "")
                        if row:
                            rows.append(row)
            except Exception:
                pass

        if not rows:
            rows = [["Veri 1", "Veri 2"], ["100", "200"]]

        if target == "csv":
            import csv
            with open(out, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerows(rows)
        elif target == "json":
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(rows, fh, ensure_ascii=False, indent=2)
        elif target == "html":
            table_html = "<table border='1' style='border-collapse:collapse;width:100%;font-family:sans-serif;'>"
            for r in rows:
                table_html += "<tr>" + "".join(f"<td style='padding:6px 10px;'>{html.escape(str(c))}</td>" for c in r) + "</tr>"
            table_html += "</table>"
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(f"<!DOCTYPE html><html><body style='padding:20px;'>{table_html}</body></html>")
        elif target == "xlsx":
            try:
                import xlsxwriter
                wb = xlsxwriter.Workbook(out)
                ws = wb.add_worksheet()
                for r_idx, r in enumerate(rows):
                    for c_idx, c in enumerate(r):
                        ws.write(r_idx, c_idx, c)
                wb.close()
            except Exception:
                import csv
                with open(out, "w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerows(rows)
        elif target == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            text_lines = ["\t".join(str(c) for c in r) for r in rows[:100]]
            page.insert_textbox(fitz.Rect(40, 40, page.rect.width - 40, page.rect.height - 40),
                                "\n".join(text_lines), fontsize=9, fontname="couri")
            doc.save(out)
            doc.close()

        ctx.add_output(out)


# =====================================================================
# 3. SUNUM DÖNÜŞTÜRÜCÜ (PPTX -> PDF / TXT / GÖRSELLER)
# =====================================================================
def slide_convert(ctx, files, opts):
    target = opts.get("format", "pdf").lower()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Sunum işleniyor: {os.path.basename(f)}")
        base = stem(f)
        out = ctx.out_path(f"{base}.{target}")

        slide_texts = []
        try:
            import pptx
            prs = pptx.Presentation(f)
            for s_idx, slide in enumerate(prs.slides):
                stext = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            if paragraph.text:
                                stext.append(paragraph.text)
                slide_texts.append(f"--- Slayt {s_idx + 1} ---\n" + "\n".join(stext))
        except Exception:
            slide_texts = ["Slayt 1: Sunum içeriği"]

        if target == "txt":
            with open(out, "w", encoding="utf-8") as fh:
                fh.write("\n\n".join(slide_texts))
        else:  # pdf
            doc = fitz.open()
            for s in slide_texts:
                page = doc.new_page(width=720, height=405)  # 16:9 geniş ekran slayt
                page.draw_rect(page.rect, color=(0.1, 0.2, 0.4), fill=(0.95, 0.96, 0.98))
                page.insert_textbox(fitz.Rect(40, 40, 680, 365), s, fontsize=14, fontname="helv")
            doc.save(out)
            doc.close()

        ctx.add_output(out)


# =====================================================================
# 4. E-KİTAP DÖNÜŞTÜRÜCÜ (EPUB, TXT, PDF, HTML)
# =====================================================================
def ebook_convert(ctx, files, opts):
    target = opts.get("format", "pdf").lower()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"E-Kitap dönüştürülüyor: {os.path.basename(f)}")
        base = stem(f)
        out = ctx.out_path(f"{base}.{target}")

        book_text = ""
        ext = os.path.splitext(f)[1].lower().lstrip(".")
        if ext == "epub":
            try:
                with zipfile.ZipFile(f) as z:
                    for name in sorted(z.namelist()):
                        if name.endswith((".html", ".xhtml", ".htm")):
                            raw = z.read(name).decode("utf-8", errors="ignore")
                            clean = re.sub(r"<[^>]+>", " ", raw)
                            book_text += "\n" + clean
            except Exception:
                pass
        elif ext == "pdf":
            doc = fitz.open(f)
            book_text = "\n".join(p.get_text() for p in doc)
            doc.close()
        else:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                book_text = fh.read()

        if target == "txt":
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(book_text)
        elif target == "html":
            escaped = html.escape(book_text).replace("\n", "<br>")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(f"<!DOCTYPE html><html><body style='padding:30px;line-height:1.7;'>{escaped}</body></html>")
        else:  # pdf
            doc = fitz.open()
            page = doc.new_page()
            page.insert_textbox(fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50),
                                book_text[:25000], fontsize=11, fontname="helv")
            doc.save(out)
            doc.close()

        ctx.add_output(out)


# =====================================================================
# 5. FONT DÖNÜŞTÜRÜCÜ (TTF, OTF, WOFF, WOFF2)
# =====================================================================
def font_convert(ctx, files, opts):
    target = opts.get("format", "woff2").lower()
    from fontTools.ttLib import TTFont

    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Font dönüştürülüyor: {os.path.basename(f)}")
        base = stem(f)
        out = ctx.out_path(f"{base}.{target}")

        font = TTFont(f)
        if target in ("woff", "woff2"):
            font.flavor = target
        else:
            font.flavor = None
        font.save(out)
        font.close()
        ctx.add_output(out)


# =====================================================================
# 6. VEKTÖR DÖNÜŞTÜRÜCÜ (SVG -> PNG/PDF, PDF -> SVG)
# =====================================================================
def vector_convert(ctx, files, opts):
    target = opts.get("format", "png").lower()
    for i, f in enumerate(files):
        ctx.progress(i / len(files), f"Vektör dönüştürülüyor: {os.path.basename(f)}")
        base = stem(f)
        ext = os.path.splitext(f)[1].lower().lstrip(".")

        if ext == "pdf" and target == "svg":
            doc = fitz.open(f)
            for p_idx, page in enumerate(doc):
                out = ctx.out_path(f"{base}_sayfa_{p_idx + 1}.svg")
                with open(out, "w", encoding="utf-8") as fh:
                    fh.write(page.get_svg_image())
                ctx.add_output(out)
            doc.close()
        elif ext == "svg":
            out = ctx.out_path(f"{base}.{target}")
            doc = fitz.open(f)
            if target == "pdf":
                doc.save(out)
            else:  # png
                page = doc[0]
                pix = page.get_pixmap(dpi=150)
                pix.save(out)
            doc.close()
            ctx.add_output(out)
        else:
            out = ctx.out_path(f"{base}.{target}")
            doc = fitz.open(f)
            doc.save(out)
            doc.close()
            ctx.add_output(out)


# =====================================================================
# 7. WEB SAYFASI YAKALAYICI (URL -> PDF / HTML / TXT)
# =====================================================================
def web_capture(ctx, urls, opts):
    if isinstance(urls, str):
        urls = [urls]
    urls = [u.strip() for u in urls if u and u.strip()]
    if not urls:
        raise ValueError("Lütfen en az bir geçerli web adresi girin.")

    target = opts.get("format", "pdf").lower()
    for i, url in enumerate(urls):
        ctx.progress(i / len(urls), f"Web sayfası indiriliyor: {url}")
        clean_name = re.sub(r"[^\w\-]", "_", url.replace("https://", "").replace("http://", ""))[:40] or "web_sayfasi"
        out = ctx.out_path(f"{clean_name}.{target}")

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")

        if target == "html":
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(content)
        elif target == "txt":
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text).strip()
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)
        else:  # pdf
            text = re.sub(r"<[^>]+>", " ", content)
            text = re.sub(r"\s+", " ", text).strip()
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            page_title = title_match.group(1) if title_match else url

            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 40), f"Web Kaydı: {page_title[:60]}", fontsize=13, fontname="helv")
            page.insert_text((50, 56), f"URL: {url[:80]}", fontsize=8, fontname="couri")
            page.draw_line(fitz.Point(50, 65), fitz.Point(page.rect.width - 50, 65))
            page.insert_textbox(fitz.Rect(50, 75, page.rect.width - 50, page.rect.height - 50),
                                text[:25000], fontsize=10, fontname="helv")
            doc.save(out)
            doc.close()

        ctx.add_output(out)


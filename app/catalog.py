"""Araç kataloğu: tüm araçlar tek bir yerden tanımlanır.
Arayüz bu listeyi okuyup menüleri, kartları ve ayar formlarını otomatik oluşturur."""
from .tools import downloader, media, image, archive, pdf, documents
PDF_EXT = ["pdf"]

VIDEO_EXT = ["mp4", "mkv", "webm", "avi", "mov", "flv", "wmv", "mpeg", "mpg", "3gp", "ts", "m4v", "ogv", "mts", "m2ts", "vob"]
AUDIO_EXT = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff", "ac3", "amr", "mka"]
IMAGE_EXT = ["jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff", "tif", "ico", "avif", "heic", "heif", "jfif", "tga", "ppm"]
ARCHIVE_EXT = ["zip", "tar", "gz", "tgz", "bz2", "xz", "7z"]
OFFICE_EXT = ["doc", "docx", "odt", "rtf", "txt", "xls", "xlsx", "ods", "csv", "ppt", "pptx", "odp"]


def sel(id, label, choices, default=None, **kw):
    ch = [list(c) if isinstance(c, (list, tuple)) else [c, str(c).upper()] for c in choices]
    return {"id": id, "label": label, "type": "select", "choices": ch,
            "default": default if default is not None else ch[0][0], **kw}


def rng(id, label, mn, mx, default, step=1, suffix="", **kw):
    return {"id": id, "label": label, "type": "range", "min": mn, "max": mx, "step": step,
            "default": default, "suffix": suffix, **kw}


def txt(id, label, default="", placeholder="", **kw):
    return {"id": id, "label": label, "type": "text", "default": default, "placeholder": placeholder, **kw}


def num(id, label, default, mn=None, mx=None, **kw):
    return {"id": id, "label": label, "type": "number", "default": default, "min": mn, "max": mx, **kw}


def chk(id, label, default=False, **kw):
    return {"id": id, "label": label, "type": "checkbox", "default": default, **kw}


RES = sel("resolution", "Çözünürlük", [["orig", "Orijinal"], ["2160", "4K (2160p)"], ["1440", "1440p"],
                                       ["1080", "1080p"], ["720", "720p"], ["480", "480p"], ["360", "360p"]])
FPS = sel("fps", "Kare hızı (FPS)", [["orig", "Orijinal"], "60", "30", "25", "24", "15"])
BITRATE = sel("bitrate", "Bit hızı", [["320", "320 kbps"], ["256", "256 kbps"], ["192", "192 kbps"],
                                     ["128", "128 kbps"], ["96", "96 kbps"]], "192")
DL_OPTIONS = [
    sel("mode", "İndirme türü", [["video", "🎬 Video"], ["audio", "🎵 Sadece Ses"]]),
    sel("quality", "Video kalitesi", [["best", "En İyi"], ["2160", "4K"], ["1440", "1440p"], ["1080", "1080p"],
                                      ["720", "720p"], ["480", "480p"], ["360", "360p"]], show_if={"mode": ["video"]}),
    sel("container", "Video formatı", ["mp4", "mkv", "webm"], show_if={"mode": ["video"]}),
    sel("audio_format", "Ses formatı", ["mp3", "m4a", "wav", "flac", "opus"], show_if={"mode": ["audio"]}),
    dict(BITRATE, show_if={"mode": ["audio"], "audio_format": ["mp3", "m4a", "opus"]}),
    chk("playlist", "Oynatma listesinin tamamını indir"),
    chk("subtitles", "Altyazıları da indir (TR/EN)", show_if={"mode": ["video"]}),
    chk("thumbnail", "Kapak görselini kaydet"),
]

C = {  # kategoriler: id -> (başlık, grup, ikon)
    "dl": ("İndiriciler", "İNDİRME", "⬇️"),
    "video": ("Video Araçları", "DÖNÜŞTÜRÜCÜ", "🎬"),
    "audio": ("Ses Araçları", "DÖNÜŞTÜRÜCÜ", "🎵"),
    "image": ("Görsel Araçları", "DÖNÜŞTÜRÜCÜ", "🖼️"),
    "doc": ("Belge & Ofis", "DÖNÜŞTÜRÜCÜ", "📄"),
    "archive": ("Arşiv", "DÖNÜŞTÜRÜCÜ", "🗜️"),
    "pdf-org": ("PDF Düzenle", "PDF ARAÇLARI", "📑"),
    "pdf-opt": ("PDF Optimize", "PDF ARAÇLARI", "⚡"),
    "pdf-to": ("PDF'e Dönüştür", "PDF ARAÇLARI", "📥"),
    "pdf-from": ("PDF'ten Dönüştür", "PDF ARAÇLARI", "📤"),
    "pdf-edit": ("PDF Düzenleme", "PDF ARAÇLARI", "✏️"),
    "pdf-sec": ("PDF Güvenlik", "PDF ARAÇLARI", "🔒"),
}


def T(id, cat, name, desc, icon, color, handler=None, input="files", accept=None, multiple=True,
      options=None, requires=None, min_files=1):
    return {"id": id, "category": cat, "name": name, "desc": desc, "icon": icon, "color": color,
            "handler": handler, "input": input, "accept": accept, "multiple": multiple,
            "options": options or [], "requires": requires or [], "min_files": min_files}


TOOLS = [
    # ---------------- İNDİRİCİLER ----------------
    T("dl_youtube", "dl", "YouTube İndirici", "Video, Shorts ve oynatma listelerini MP4/MP3 olarak indir.",
      "▶️", "#e53935", downloader.download, input="url", options=DL_OPTIONS, requires=["ffmpeg"]),
    T("dl_instagram", "dl", "Instagram İndirici", "Reels, gönderi ve video içeriklerini indir.",
      "📸", "#d62976", downloader.download, input="url", options=DL_OPTIONS, requires=["ffmpeg"]),
    T("dl_tiktok", "dl", "TikTok İndirici", "TikTok videolarını indir.", "🎶", "#25f4ee",
      downloader.download, input="url", options=DL_OPTIONS, requires=["ffmpeg"]),
    T("dl_twitter", "dl", "X / Twitter İndirici", "Tweet içindeki videoları indir.", "🐦", "#1d9bf0",
      downloader.download, input="url", options=DL_OPTIONS, requires=["ffmpeg"]),
    T("dl_universal", "dl", "Evrensel İndirici", "Facebook, Vimeo, Twitch, SoundCloud, Reddit ve 1000+ site.",
      "🌐", "#7e57c2", downloader.download, input="url", options=DL_OPTIONS, requires=["ffmpeg"]),

    # ---------------- VİDEO ----------------
    T("video_convert", "video", "Video Dönüştür", "MP4, MKV, WEBM, AVI, MOV, WMV, FLV, 3GP, OGV... arası dönüşüm.",
      "🎞️", "#1e88e5", media.video_convert, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("format", "Hedef format", ["mp4", "mkv", "webm", "avi", "mov", "wmv", "flv", "m4v", "mpeg", "3gp", "ts", "ogv"]),
          sel("vcodec", "Video kodeği", [["auto", "Otomatik"], ["h264", "H.264"], ["h265", "H.265 / HEVC"],
                                         ["vp9", "VP9"], ["av1", "AV1 (yavaş)"], ["copy", "Kopyala (yeniden kodlama yok)"]]),
          dict(RES, show_if={"vcodec": ["auto", "h264", "h265", "vp9", "av1"]}),
          dict(FPS, show_if={"vcodec": ["auto", "h264", "h265", "vp9", "av1"]}),
          rng("crf", "Kalite (düşük = daha iyi)", 16, 35, 23, show_if={"vcodec": ["auto", "h264", "h265", "vp9", "av1"]}),
          chk("mute", "Sesi kaldır", show_if={"vcodec": ["auto", "h264", "h265", "vp9", "av1"]}),
      ]),
    T("video_compress", "video", "Video Sıkıştır", "Kaliteyi koruyarak video boyutunu küçült.",
      "🗜️", "#43a047", media.video_compress, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("level", "Sıkıştırma", [["light", "Hafif (yüksek kalite)"], ["medium", "Orta (önerilen)"],
                                      ["strong", "Güçlü (küçük boyut)"], ["size", "Hedef boyut (MB)"]], "medium"),
          num("target_mb", "Hedef boyut (MB)", 25, 1, 10000, show_if={"level": ["size"]}),
          RES,
      ]),
    T("video_trim", "video", "Video / Ses Kes", "Başlangıç ve bitiş zamanı vererek kesit al.",
      "✂️", "#fb8c00", media.media_trim, accept=VIDEO_EXT + AUDIO_EXT, requires=["ffmpeg"], options=[
          txt("start", "Başlangıç (ss veya dd:ss)", "00:00", "00:00"),
          txt("end", "Bitiş (boş = sona kadar)", "", "01:30"),
          chk("precise", "Kare hassasiyetinde kes (yeniden kodlar)", True),
      ]),
    T("video_merge", "video", "Video Birleştir", "Birden fazla videoyu sırayla tek videoda birleştir.",
      "🔗", "#8e24aa", media.video_merge, accept=VIDEO_EXT, requires=["ffmpeg"], min_files=2, options=[
          sel("height", "Çıktı çözünürlüğü", [["1080", "1080p"], ["720", "720p"], ["480", "480p"]], "720"),
      ]),
    T("video_gif", "video", "Videodan GIF", "Videonun bir bölümünü yüksek kaliteli GIF'e çevir.",
      "🌀", "#00acc1", media.video_to_gif, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          txt("start", "Başlangıç", "00:00"), txt("length", "Süre (saniye, 0 = tamamı)", "5"),
          rng("fps", "FPS", 5, 30, 12), rng("width", "Genişlik", 160, 1280, 480, 20, "px"),
      ]),
    T("video_extract_audio", "video", "Videodan Ses Çıkar", "Videonun sesini MP3, WAV, FLAC... olarak al.",
      "🎧", "#5e35b1", media.audio_convert, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("format", "Ses formatı", ["mp3", "wav", "flac", "m4a", "ogg", "opus", "aac"]), BITRATE,
      ]),
    T("video_mute", "video", "Videonun Sesini Kaldır", "Videodaki sesi tamamen sil (kalite kaybı yok).",
      "🔇", "#757575", media.video_mute, accept=VIDEO_EXT, requires=["ffmpeg"]),
    T("video_rotate", "video", "Video Döndür / Çevir", "90°, 180° döndür veya ayna çevir.",
      "🔄", "#3949ab", media.video_rotate, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("rotation", "İşlem", [["90", "90° sağa"], ["270", "90° sola"], ["180", "180°"],
                                    ["hflip", "Yatay ayna"], ["vflip", "Dikey ayna"]]),
      ]),
    T("video_speed", "video", "Video Hızı", "Videoyu hızlandır veya yavaşlat.",
      "⏩", "#f4511e", media.video_speed, accept=VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("speed", "Hız", [["0.25", "0.25x"], ["0.5", "0.5x"], ["0.75", "0.75x"], ["1.25", "1.25x"],
                               ["1.5", "1.5x"], ["2", "2x"], ["4", "4x"]], "2"),
      ]),

    # ---------------- SES ----------------
    T("audio_convert", "audio", "Ses Dönüştür", "MP3, WAV, FLAC, AAC, M4A, OGG, OPUS, WMA, AIFF, AC3...",
      "🎵", "#8e24aa", media.audio_convert, accept=AUDIO_EXT + VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("format", "Hedef format", ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma", "aiff", "ac3"]),
          dict(BITRATE, show_if={"format": ["mp3", "aac", "m4a", "ogg", "opus", "wma", "ac3"]}),
          sel("samplerate", "Örnekleme hızı", [["orig", "Orijinal"], ["48000", "48 kHz"], ["44100", "44.1 kHz"],
                                                ["22050", "22 kHz"]]),
          sel("channels", "Kanal", [["orig", "Orijinal"], ["2", "Stereo"], ["1", "Mono"]]),
      ]),
    T("audio_merge", "audio", "Ses Birleştir", "Birden fazla ses dosyasını tek dosyada birleştir.",
      "🔗", "#d81b60", media.audio_merge, accept=AUDIO_EXT, requires=["ffmpeg"], min_files=2, options=[
          sel("format", "Çıktı formatı", ["mp3", "wav", "flac", "m4a", "ogg"]),
      ]),
    T("audio_trim", "audio", "Ses Kes", "Ses dosyasından istediğin bölümü kes.",
      "✂️", "#fb8c00", media.media_trim, accept=AUDIO_EXT, requires=["ffmpeg"], options=[
          txt("start", "Başlangıç", "00:00"), txt("end", "Bitiş (boş = sona kadar)", ""),
          chk("precise", "Hassas kes (yeniden kodlar)", True),
      ]),
    T("audio_volume", "audio", "Ses Seviyesi", "Ses seviyesini normalize et veya artır/azalt.",
      "🔊", "#00897b", media.audio_volume, accept=AUDIO_EXT + VIDEO_EXT, requires=["ffmpeg"], options=[
          sel("mode", "Mod", [["normalize", "Otomatik normalize (EBU R128)"], ["db", "Manuel (dB)"]]),
          rng("db", "Değişim", -20, 20, 5, 1, " dB", show_if={"mode": ["db"]}),
      ]),

    # ---------------- GÖRSEL ----------------
    T("image_convert", "image", "Görsel Dönüştür", "JPG, PNG, WEBP, AVIF, GIF, BMP, TIFF, ICO, HEIC → her yöne.",
      "🖼️", "#00897b", image.image_convert, accept=IMAGE_EXT, options=[
          sel("format", "Hedef format", ["png", "jpg", "webp", "avif", "gif", "bmp", "tiff", "ico", "pdf", "tga"]),
          rng("quality", "Kalite", 10, 100, 90, 1, "%", show_if={"format": ["jpg", "webp", "avif"]}),
      ]),
    T("image_compress", "image", "Görsel Sıkıştır", "JPG, PNG, WEBP görsellerin boyutunu küçült.",
      "📉", "#43a047", image.image_compress, accept=IMAGE_EXT, options=[
          rng("quality", "Kalite", 10, 95, 70, 1, "%"),
          num("max_side", "En uzun kenar (px, 0 = değiştirme)", 0, 0, 20000),
      ]),
    T("image_resize", "image", "Görsel Boyutlandır", "Yüzde veya piksel ile yeniden boyutlandır.",
      "📐", "#1e88e5", image.image_resize, accept=IMAGE_EXT, options=[
          sel("mode", "Yöntem", [["percent", "Yüzde"], ["width", "Genişliğe göre"], ["height", "Yüksekliğe göre"],
                                 ["exact", "Tam boyut"]]),
          rng("percent", "Ölçek", 5, 400, 50, 5, "%", show_if={"mode": ["percent"]}),
          num("width", "Genişlik (px)", 1280, 1, 20000, show_if={"mode": ["width", "exact"]}),
          num("height", "Yükseklik (px)", 720, 1, 20000, show_if={"mode": ["height", "exact"]}),
      ]),
    T("image_rotate", "image", "Görsel Döndür", "Görselleri döndür veya aynala.", "🔄", "#3949ab",
      image.image_rotate, accept=IMAGE_EXT, options=[
          sel("rotation", "İşlem", [["90", "90° sağa"], ["270", "90° sola"], ["180", "180°"],
                                    ["hflip", "Yatay ayna"], ["vflip", "Dikey ayna"]]),
      ]),

    # ---------------- ARŞİV ----------------
    T("archive_create", "archive", "Arşiv Oluştur", "Dosyaları ZIP, TAR.GZ, TAR.XZ arşivine sıkıştır.",
      "🗜️", "#6d4c41", archive.archive_create, options=[
          sel("format", "Format", ["zip", "tar.gz", "tar.xz", "tar.bz2", "tar"]),
          txt("name", "Arşiv adı", "", "arsiv"),
          rng("level", "Sıkıştırma seviyesi", 0, 9, 6, show_if={"format": ["zip"]}),
      ]),
    T("archive_extract", "archive", "Arşiv Çıkar", "ZIP, TAR, GZ, 7Z arşivlerini klasöre çıkar.",
      "📂", "#8d6e63", archive.archive_extract, accept=ARCHIVE_EXT),

    # ---------------- BELGE & OFİS ----------------
    T("doc_convert", "doc", "Belge Dönüştür", "DOCX, ODT, RTF, TXT, HTML, MD arası dönüşüm.", "📝", "#1565c0",
      documents.doc_convert, accept=OFFICE_EXT, options=[
          sel("format", "Hedef format", [["pdf", "PDF Belgesi"], ["docx", "Word (DOCX)"], ["txt", "Düz Metin (TXT)"], ["html", "Web Sayfası (HTML)"]]),
      ]),
    T("sheet_convert", "doc", "Tablo Dönüştür", "XLSX, XLS, ODS, CSV arası dönüşüm.", "📊", "#2e7d32",
      documents.sheet_convert, accept=OFFICE_EXT, options=[
          sel("format", "Hedef format", [["csv", "CSV (Virgülle Ayrılmış)"], ["xlsx", "Excel (XLSX)"], ["json", "JSON Verisi"], ["html", "HTML Tablosu"], ["pdf", "PDF Belgesi"]]),
      ]),
    T("slide_convert", "doc", "Sunum Dönüştür", "PPTX, PPT, ODP sunumlarını PDF veya metne çevir.", "📽️", "#d84315",
      documents.slide_convert, accept=OFFICE_EXT, options=[
          sel("format", "Hedef format", [["pdf", "PDF Sunumu (16:9)"], ["txt", "Slayt Metinleri (TXT)"]]),
      ]),
    T("ebook_convert", "doc", "E-Kitap Dönüştür", "EPUB, FB2, TXT, PDF e-kitap dönüşümü.", "📚", "#6a1b9a",
      documents.ebook_convert, accept=["epub", "fb2", "txt", "pdf"], options=[
          sel("format", "Hedef format", [["pdf", "PDF Belgesi"], ["txt", "Düz Metin (TXT)"], ["html", "HTML Kitap"]]),
      ]),
    T("font_convert", "doc", "Font Dönüştür", "TTF, OTF, WOFF, WOFF2 arası dönüşüm.", "🔤", "#455a64",
      documents.font_convert, accept=["ttf", "otf", "woff", "woff2"], options=[
          sel("format", "Hedef format", [["woff2", "WOFF2 (Web Font)"], ["woff", "WOFF (Klasik Web)"], ["ttf", "TTF (TrueType)"], ["otf", "OTF (OpenType)"]]),
      ]),
    T("vector_convert", "doc", "Vektör Dönüştür", "SVG → PNG/PDF, PDF → SVG dönüşümü.", "✒️", "#ef6c00",
      documents.vector_convert, accept=["svg", "pdf"], options=[
          sel("format", "Hedef format", [["png", "PNG Görseli (Raster)"], ["pdf", "PDF Vektör"], ["svg", "SVG Vektör Çizimi"]]),
      ]),
    T("web_capture", "doc", "Web Sayfası Yakala", "Bir web sayfasını PDF, HTML veya metin olarak kaydet.", "🌍", "#0277bd",
      documents.web_capture, input="url", options=[
          sel("format", "Kayıt formatı", [["pdf", "PDF Belgesi"], ["html", "Tam HTML Sayfası"], ["txt", "Sayfa Metni (TXT)"]]),
      ]),

    # ---------------- PDF (iLovePDF & Office) ----------------
    T("pdf_merge", "pdf-org", "PDF Birleştir", "Birden fazla PDF'i istediğin sırayla birleştir.", "🔗", "#e53935",
      pdf.pdf_merge, accept=PDF_EXT, min_files=2),
    T("pdf_split", "pdf-org", "PDF Böl", "Sayfa aralıklarına göre PDF'i ayır.", "✂️", "#e53935",
      pdf.pdf_split, accept=PDF_EXT, options=[
          txt("ranges", "Sayfa Aralıkları (örn: 1-3, 5, 8-10)", "", "Tüm sayfaları ayırmak için boş bırakın"),
      ]),
    T("pdf_remove", "pdf-org", "Sayfa Sil", "PDF'ten istemediğin sayfaları kaldır.", "🗑️", "#e53935",
      pdf.pdf_remove, accept=PDF_EXT, options=[
          txt("pages", "Silinecek Sayfalar (örn: 1, 3, 5)", "", "Örn: 2, 4"),
      ]),
    T("pdf_compress", "pdf-opt", "PDF Sıkıştır", "Kaliteyi koruyarak PDF boyutunu küçült.", "🗜️", "#43a047",
      pdf.pdf_compress, accept=PDF_EXT, options=[
          sel("level", "Sıkıştırma Seviyesi", [["medium", "Önerilen Sıkıştırma (İyi Kalite)"], ["extreme", "Yüksek Sıkıştırma (En Küçük Boyut)"]]),
      ]),
    T("pdf_repair", "pdf-opt", "PDF Onar", "Bozuk veya hasarlı PDF dosyalarını kurtar.", "🛠️", "#43a047",
      pdf.pdf_repair, accept=PDF_EXT),
    T("pdf_ocr", "pdf-opt", "OCR PDF", "Taranmış PDF'i aranabilir metne çevir (RapidOCR).", "🔍", "#43a047",
      pdf.pdf_ocr, accept=PDF_EXT),
    T("jpg_to_pdf", "pdf-to", "JPG'den PDF'e", "Görselleri tek bir PDF belgesine dönüştür.", "🖼️", "#fbc02d",
      pdf.jpg_to_pdf, accept=IMAGE_EXT),
    T("word_to_pdf", "pdf-to", "Word'den PDF'e", "DOC/DOCX dosyalarını doğrudan PDF'e çevir.", "📘", "#1565c0",
      pdf.office_to_pdf, accept=["doc", "docx", "odt", "rtf"]),
    T("ppt_to_pdf", "pdf-to", "PowerPoint'ten PDF'e", "PPT/PPTX sunumlarını PDF'e çevir.", "📙", "#d84315",
      pdf.office_to_pdf, accept=["ppt", "pptx", "odp"]),
    T("excel_to_pdf", "pdf-to", "Excel'den PDF'e", "XLS/XLSX tablolarını PDF'e çevir.", "📗", "#2e7d32",
      pdf.office_to_pdf, accept=["xls", "xlsx", "ods", "csv"]),
    T("pdf_to_jpg", "pdf-from", "PDF'ten JPG'ye", "Her sayfayı yüksek kaliteli görsele çevir.", "🖼️", "#fbc02d",
      pdf.pdf_to_jpg, accept=PDF_EXT, options=[
          sel("format", "Görsel Formatı", ["jpg", "png", "webp"]),
          sel("dpi", "Çözünürlük (DPI)", [["150", "Standart (150 DPI)"], ["300", "Yüksek Kalite (300 DPI)"], ["72", "Web (72 DPI)"]], "150"),
      ]),
    T("pdf_to_word", "pdf-from", "PDF'ten Word'e", "PDF'i düzenlenebilir DOCX belgesine çevir.", "📘", "#1565c0",
      pdf.pdf_to_word, accept=PDF_EXT),
    T("pdf_rotate", "pdf-edit", "PDF Döndür", "Sayfaları istediğin yöne döndür.", "🔄", "#7b1fa2",
      pdf.pdf_rotate, accept=PDF_EXT, options=[
          sel("angle", "Döndürme Açısı", [["90", "90° Sağa"], ["180", "180° Ters"], ["270", "90° Sola"]], "90"),
      ]),
    T("pdf_numbers", "pdf-edit", "Sayfa Numarası Ekle", "Sayfaların altına otomatik sayfa numarası bas.", "🔢", "#7b1fa2",
      pdf.pdf_numbers, accept=PDF_EXT, options=[
          sel("position", "Numara Konumu", [["bottom-right", "Alt Sağ"], ["bottom-center", "Alt Orta"], ["bottom-left", "Alt Sol"]]),
      ]),
    T("pdf_watermark", "pdf-edit", "Filigran Ekle", "PDF sayfalarına metin filigranı ekle.", "💧", "#7b1fa2",
      pdf.pdf_watermark, accept=PDF_EXT, options=[
          txt("text", "Filigran Metni", "GİZLİ / CONFIDENTIAL"),
          rng("opacity", "Saydamlık", 0.1, 1.0, 0.3, 0.1),
          rng("size", "Yazı Boyutu", 18, 72, 36, 2, "pt"),
      ]),
    T("pdf_protect", "pdf-sec", "PDF Şifrele", "PDF belgesine açılış parolası koy.", "🔒", "#00838f",
      pdf.pdf_protect, accept=PDF_EXT, options=[
          txt("password", "Parola", "", "Şifrenizi yazın..."),
      ]),
    T("pdf_unlock", "pdf-sec", "PDF Kilidi Aç", "PDF şifresini kaldır ve kilitsiz kaydet.", "🔓", "#00838f",
      pdf.pdf_unlock, accept=PDF_EXT, options=[
          txt("password", "Mevcut Parola (varsa)", "", "Parolayı girin..."),
      ]),
]

TOOL_MAP = {t["id"]: t for t in TOOLS}

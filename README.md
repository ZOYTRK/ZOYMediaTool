# ZOY Media Tool 🧰

**ZOY Media Tool**, Windows XP ve Windows 2000 retro masaüstü estetiğinde geliştirilmiş; medya indirme, video/ses/görsel dönüştürme, arşivleme ve kapsamlı PDF yönetim araç kutusudur.

---

## ✨ Özellikler

### 🎨 Retro & Modern Arayüz
- **4 Nostaljik Tema:**
  - **Windows 2000 Klasik:** Otantik 3D gri pencereler ve klasik Windows mavi başlıkları.
  - **Windows 2000 Koyu:** Koyu gri / antrasit retro 3D tasarım.
  - **Windows XP Koyu:** Modern karanlık mod ile XP stilinin harmanı.
  - **Windows XP Luna:** Klasik XP mavi pencere ve Bliss tepe duvar kağıdı teması.
- **Dinamik Başlat Menüsü:** Tüm temalarla senkronize çalışan retro başlat menüsü, hızlı erişim ve sistem ayarları.
- **Sürükle & Bırak:** Dosyaları doğrudan pencereye sürükleyip anında işleme koyma.
- **İşlem Kuyruğu:** Eşzamanlı arka plan işlemleri, canlı ilerleme çubuğu ve anlık iptal desteği.
- **XP Balon Bildirimleri:** Tamamlanan işlemler için retro sesli/görsel sistem tepsisi bildirimleri.

---

### 🧰 Araç Kataloğu (48+ Araç)

#### 1. ⬇️ İndiriciler
- **YouTube İndirici:** Video, Shorts ve oynatma listelerini en yüksek kalitede MP4 veya MP3 olarak indirme.
- **Instagram İndirici:** Reels, video ve gönderi içeriklerini kolayca indirme.
- **TikTok & Twitter/X & Diğerleri:** 1000+ siteden tek tıkla medya çekme.

#### 2. 🎬 Video Araçları
- **Video Dönüştür:** MP4, MKV, WEBM, AVI, MOV, FLV, WMV, 3GP vb. formatlar arası kayıpsız dönüştürme.
- **Video Sıkıştır:** Kaliteyi koruyarak dosya boyutunu küçültme.
- **Video Kırp & Kes:** Başlangıç ve bitiş zamanına göre hassas video kesme.
- **Video Birleştir:** Birden fazla video dosyasını tek bir videoda birleştirme.
- **GIF Oluşturucu:** Videolardan akıcı animasyonlu GIF üretme.
- **Sesi Kaldır / Sessize Al:** Videodaki ses kanalını sıfırlama.
- **Sesi Çıkar:** Videodan sesi bağımsız MP3/WAV/AAC dosyası olarak alma.
- **Video Döndür:** 90°, 180°, 270° yön düzeltme.

#### 3. 🎵 Ses Araçları
- **Ses Dönüştür:** MP3, WAV, FLAC, AAC, M4A, OGG, OPUS, WMA formatları arası dönüştürme.
- **Ses Sıkıştır:** Bit hızı optimizasyonu ile boyut tasarrufu.
- **Ses Kırp & Kes:** İstenen aralığı kayıpsız ayırma.
- **Ses Birleştir:** Ses kayıtlarını ardışık bağlama.
- **Ses Normalizasyonu:** Ses seviyesini standart EBU R128 seviyesine dengeleme.

#### 4. 🖼️ Görsel Araçları
- **Görsel Dönüştür:** JPG, PNG, WEBP, ICO, AVIF, HEIC, BMP, TIFF formatları arası toplu dönüştürme.
- **Görsel Sıkıştır:** Web için optimize edilmiş boyut tasarrufu.
- **Yeniden Boyutlandır:** Piksel veya yüzde bazında ölçekleme.
- **Görsel Döndür & Çevir:** Yön ve açı ayarlama.

#### 5. 📑 PDF & Belge Araçları
- **PDF Birleştir & Böl:** Sayfaları birleştirme, ayırma veya belirli aralıkları çıkarma.
- **PDF Sıkıştır:** Vektör ve görselleri yeniden örnekleyerek boyutu küçültme.
- **PDF Sayfa Numaralandır:** Sayfa numaralarını konuma ve biçime göre ekleme.
- **PDF Filigran:** Metin tabanlı filigran yerleştirme.
- **PDF Güvenlik:** PDF şifreleme ve parola korumasını kaldırma.
- **PDF'ten Görsele:** Sayfaları yüksek çözünürlüklü JPG/PNG olarak kaydetme.
- **Görsellerden PDF:** Fotoğrafları tek bir PDF dokümanında toplama.
- **PDF'ten Word'e & Word'den PDF'e:** Doküman dönüştürme (Word veya harici Office kurulumu gerektirmeden saf Python fallback desteği ile).
- **PDF OCR & Onarma:** Taranmış belgeleri aranabilir metne dönüştürme ve hasarlı PDF'leri kurtarma.

#### 6. 🗜️ Arşiv Araçları
- **Arşiv Oluştur:** Dosya ve klasörleri ZIP, TAR, TAR.GZ, TAR.XZ formatlarında paketleme.
- **Arşiv Aç:** Sıkıştırılmış arşivleri klasöre çıkartma.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/ZOYTRK/ZOYMediaTool.git
cd ZOYMediaTool
```

### 2. Bağımlılıkları Yükleyin
Python 3.10 veya üzeri tavsiye edilir:
```bash
pip install -r requirements.txt
```

### 3. FFmpeg Hazırlığı
Medya ve ses işlemleri için FFmpeg gereklidir:
- **Windows:** `ffmpeg.exe` ve `ffprobe.exe` dosyalarını doğrudan projenin kök dizinine koyabilir veya sistem `PATH` ortam değişkenine ekleyebilirsiniz.
- [ffmpeg.org/download.html](https://ffmpeg.org/download.html) veya `winget install Gyan.FFmpeg` ile kolayca edinebilirsiniz.

### 4. Uygulamayı Başlatın
```bash
python main.py
```

---

## 🔒 Güvenlik ve Gizlilik
- Tüm işlemler **tamamen yerel (local)** makinenizde gerçekleşir. Hiçbir dosya veya veri üçüncü taraf sunuculara gönderilmez.
- Kod tabanında hiçbir kişisel dosya yolu, kullanıcı bilgisi veya sabit sürücü referansı bulunmaz. Yollar dinamik olarak işletim sistemi standartlarına (`%APPDATA%`, `Path.home()`) göre belirlenir.

---

## 📄 Lisans
Bu proje açık kaynaklıdır ve MIT lisansı altında dağıtılmaktadır.

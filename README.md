```markdown
# ZOY MediaTool

YouTube ve Instagram üzerinden medya indirme ve dosya dönüştürme aracı. (Son kullanıcılar için derlenmiş hazır sürüm sağ taraftaki **Releases** sekmesinde mevcuttur.)

## Kaynak Koddan Çalıştırma

Projeyi kaynak kod üzerinden (`main.py`) çalıştırmak için aşağıdaki adımları izleyiniz:

### 1. Kurulum
Terminal veya komut istemcisini açarak projeyi bilgisayarınıza klonlayın ve dizine girin:
```bash
git clone [https://github.com/ZOYTRK/ZOYMediaTool.git](https://github.com/ZOYTRK/ZOYMediaTool.git)
cd ZOYMediaTool

```

### 2. Bağımlılıklar (pip)

Uygulamanın ihtiyaç duyduğu Python kütüphanelerini yükleyin:

```bash
pip install -r requirements.txt

```

*(Projede kullanılan modüllere göre manuel kurulum gerekirse: `pip install <kutuphane_adi>`)*

### 3. FFmpeg Çekirdek Dosyaları

Medya işlemleri için FFmpeg gereklidir:

1. [ffmpeg.org/download.html](https://ffmpeg.org/download.html) adresinden Windows sürümünü indirin.
2. Arşiv içindeki `ffmpeg.exe` ve `ffprobe.exe` dosyalarını `main.py` dosyasının bulunduğu ana dizine kopyalayın.

### 4. Çalıştırma

Tüm hazırlıklar tamamlandıktan sonra uygulamayı başlatın:

```
python main.py

```

```

```

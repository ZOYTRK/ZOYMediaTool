import sys
import os
import customtkinter as ctk
import tkinter as tk 
from tkinter import filedialog
import threading
import re
import yt_dlp
from PIL import Image
from moviepy import VideoFileClip, AudioFileClip

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ffmpeg_yolu = resource_path("")
os.environ["PATH"] += os.pathsep + ffmpeg_yolu
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class ZoyMediaTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ZOY Media Tool")
        self.geometry("750x450")
        self.resizable(False, False)
        try:
            logo_yolu = resource_path("logo.png")
            logo_img = tk.PhotoImage(file=logo_yolu)
            self.iconphoto(False, logo_img) 
        except Exception as e:
            print(f"Logo yükleme hatası: {e}")

        self.mor_renk = "#8A2BE2" 
        self.mor_hover = "#6A5ACD" 
        self.koyu_mor = "#4B0082" 

        self.cancel_flags = {"yt": False, "ig": False}

        self.tabview = ctk.CTkTabview(
            self, 
            segmented_button_selected_color=self.mor_renk,
            segmented_button_selected_hover_color=self.mor_hover,
            segmented_button_unselected_hover_color=self.koyu_mor
        )
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_yt = self.tabview.add("YouTube Downloader")
        self.tab_ig = self.tabview.add("Instagram Downloader")
        self.tab_conv = self.tabview.add("File Converter")

        self.setup_youtube_tab()
        self.setup_instagram_tab()
        self.setup_converter_tab()

    def update_ui(self, widget, **kwargs):
        self.after(0, lambda: widget.configure(**kwargs))
        
    def update_progress(self, progress_bar, value):
        self.after(0, progress_bar.set, value)

    def cancel_download(self, tab_id):
        self.cancel_flags[tab_id] = True

    def setup_youtube_tab(self):
        self.yt_url = ctk.CTkEntry(self.tab_yt, placeholder_text="YouTube Video URL'si girin....", width=600)
        self.yt_url.pack(pady=(30, 10))

        options_frame = ctk.CTkFrame(self.tab_yt, fg_color="transparent")
        options_frame.pack(pady=10)

        self.yt_format_combo = ctk.CTkComboBox(
            options_frame, values=["Video (MP4)", "Ses (MP3)", "Ses (WAV)"], 
            command=self.update_yt_qualities,
            button_color=self.mor_renk, button_hover_color=self.mor_hover
        )
        self.yt_format_combo.pack(side="left", padx=10)

        self.yt_quality_combo = ctk.CTkComboBox(
            options_frame, values=["En İyi", "1080p", "720p", "480p", "360p"],
            button_color=self.mor_renk, button_hover_color=self.mor_hover
        )
        self.yt_quality_combo.pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(self.tab_yt, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.yt_btn = ctk.CTkButton(
            btn_frame, text="Videoyu İndir", 
            fg_color=self.mor_renk, hover_color=self.mor_hover,
            command=lambda: self.start_download("yt", self.yt_url.get(), self.yt_progress, self.yt_status, self.yt_btn, self.yt_cancel_btn)
        )
        self.yt_btn.pack(side="left", padx=10)

        self.yt_cancel_btn = ctk.CTkButton(btn_frame, text="İptal Et", fg_color="#b22222", hover_color="#8b0000", state="disabled", command=lambda: self.cancel_download("yt"))
        self.yt_cancel_btn.pack(side="left", padx=10)

        self.yt_progress = ctk.CTkProgressBar(self.tab_yt, width=600, progress_color=self.mor_renk)
        self.yt_progress.pack(pady=20)
        self.yt_progress.set(0)

        self.yt_status = ctk.CTkLabel(self.tab_yt, text="Bekleniyor...")
        self.yt_status.pack()

    def update_yt_qualities(self, choice):
        if choice == "Video (MP4)":
            self.yt_quality_combo.configure(values=["En İyi", "1080p", "720p", "480p", "360p"])
            self.yt_quality_combo.set("En İyi")
        elif choice == "Ses (MP3)":
            self.yt_quality_combo.configure(values=["320 kbps", "256 kbps", "192 kbps", "128 kbps"])
            self.yt_quality_combo.set("192 kbps")
        elif choice == "Ses (WAV)":
            self.yt_quality_combo.configure(values=["Kayıpsız (Orijinal)"])
            self.yt_quality_combo.set("Kayıpsız (Orijinal)")

    def setup_instagram_tab(self):
        self.ig_url = ctk.CTkEntry(self.tab_ig, placeholder_text="Instagram Reels/Video URL'si girin...", width=600)
        self.ig_url.pack(pady=(50, 20))

        btn_frame = ctk.CTkFrame(self.tab_ig, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.ig_btn = ctk.CTkButton(
            btn_frame, text="İçeriği İndir", 
            fg_color=self.mor_renk, hover_color=self.mor_hover,
            command=lambda: self.start_download("ig", self.ig_url.get(), self.ig_progress, self.ig_status, self.ig_btn, self.ig_cancel_btn)
        )
        self.ig_btn.pack(side="left", padx=10)

        self.ig_cancel_btn = ctk.CTkButton(btn_frame, text="İptal Et", fg_color="#b22222", hover_color="#8b0000", state="disabled", command=lambda: self.cancel_download("ig"))
        self.ig_cancel_btn.pack(side="left", padx=10)

        self.ig_progress = ctk.CTkProgressBar(self.tab_ig, width=600, progress_color=self.mor_renk)
        self.ig_progress.pack(pady=30)
        self.ig_progress.set(0)

        self.ig_status = ctk.CTkLabel(self.tab_ig, text="Bekleniyor..")
        self.ig_status.pack()

    def setup_converter_tab(self):
        self.format_label = ctk.CTkLabel(self.tab_conv, text="Hedef Formatı Seçin:")
        self.format_label.pack(pady=(40, 10))
        
        self.format_combo = ctk.CTkComboBox(
            self.tab_conv, values=["mp3", "mp4", "png", "webp", "ico"], state="readonly",
            button_color=self.mor_renk, button_hover_color=self.mor_hover
        )
        self.format_combo.set("mp3")
        self.format_combo.pack(pady=10)

        self.conv_btn = ctk.CTkButton(
            self.tab_conv, text="Dosya Seç ve Dönüştür", 
            fg_color=self.mor_renk, hover_color=self.mor_hover,
            command=self.start_conversion
        )
        self.conv_btn.pack(pady=20)

        self.conv_progress = ctk.CTkProgressBar(self.tab_conv, width=600, progress_color=self.mor_renk)
        self.conv_progress.pack(pady=20)
        self.conv_progress.set(0)

        self.conv_status = ctk.CTkLabel(self.tab_conv, text="Bekleniyor...")
        self.conv_status.pack()

    def start_download(self, tab_id, url, progress_bar, status_label, btn, cancel_btn):
        if not url:
            self.update_ui(status_label, text="Lütfen geçerli bir URL girin!", text_color="red")
            return

        target_path = filedialog.askdirectory(title="İndirilecek Klasörü Seçin")
        if not target_path:
            return 

        self.update_ui(btn, state="disabled")
        self.update_ui(cancel_btn, state="normal")
        self.update_ui(status_label, text="Bağlanıyor...", text_color="white")
        progress_bar.set(0)
        
        self.cancel_flags[tab_id] = False

        if tab_id == "yt":
            media_format = self.yt_format_combo.get()
            media_quality = self.yt_quality_combo.get()
        else:
            media_format = "Video (MP4)"
            media_quality = "En İyi"

        threading.Thread(target=self._process_download, args=(tab_id, url, target_path, progress_bar, status_label, btn, cancel_btn, media_format, media_quality), daemon=True).start()

    def _process_download(self, tab_id, url, target_path, progress_bar, status_label, btn, cancel_btn, media_format, media_quality):
        def format_size(bytes_val):
            if not bytes_val: return "0 B"
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_val < 1024.0:
                    return f"{bytes_val:.2f} {unit}"
                bytes_val /= 1024.0
            return f"{bytes_val:.2f} TB"

        def format_time(seconds):
            if not seconds: return "00:00"
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

        def progress_hook(d):
            if self.cancel_flags[tab_id]:
                raise ValueError("USER_CANCEL")

            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes')
                if not isinstance(downloaded, (int, float)): downloaded = 0

                total = d.get('total_bytes')
                if not isinstance(total, (int, float)): 
                    total = d.get('total_bytes_estimate')
                if not isinstance(total, (int, float)): total = 0

                speed = d.get('speed')
                if not isinstance(speed, (int, float)): speed = 0

                eta = d.get('eta')
                if not isinstance(eta, (int, float)): eta = 0

                down_str = format_size(downloaded)
                total_str = format_size(total) if total > 0 else "Bilinmiyor"
                speed_str = f"{format_size(speed)}/s" if speed > 0 else "0 B/s"
                eta_str = format_time(eta)

                percent = (downloaded / total * 100) if total > 0 else 0
                
                status_text = f"İndiriliyor: %{percent:.1f} | {down_str} / {total_str} | Hız: {speed_str} | Kalan: {eta_str}"
                
                self.update_ui(status_label, text=status_text, text_color="white")
                self.update_progress(progress_bar, percent / 100.0)

            elif d['status'] == 'finished':
                self.update_progress(progress_bar, 1.0)
                self.update_ui(status_label, text="Dosya işleniyor (Bu işlem biraz sürebilir)...", text_color="yellow")

        ydl_opts = {
            'outtmpl': os.path.join(target_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True
        }

        if "Video" in media_format:
            if media_quality == "En İyi":
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                res = media_quality.replace("p", "") 
                ydl_opts['format'] = f'bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        elif "Ses" in media_format:
            ydl_opts['format'] = 'bestaudio/best'
            codec = 'mp3' if "MP3" in media_format else 'wav'
            
            postprocessor = {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': codec,
            }
            
            if codec == 'mp3':
                q_val = media_quality.split(" ")[0] 
                postprocessor['preferredquality'] = q_val
                
            ydl_opts['postprocessors'] = [postprocessor]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not self.cancel_flags[tab_id]:
                self.update_ui(status_label, text="İşlem Bitti! Dosya başarıyla kaydedildi.", text_color="#00FF00")
                self.update_progress(progress_bar, 1.0)
            
        except Exception as e:
            if self.cancel_flags[tab_id] or "USER_CANCEL" in str(e):
                self.update_ui(status_label, text="İndirme İptal Edildi.", text_color="orange")
                self.update_progress(progress_bar, 0)
            else:
                self.update_ui(status_label, text="Hata! (FFmpeg yüklü değilse ses dönüşümü çalışmaz)", text_color="red")
                print(f"Hata detayı: {e}")
        finally:
            self.update_ui(btn, state="normal")
            self.update_ui(cancel_btn, state="disabled")

    def start_conversion(self):
        target_format = self.format_combo.get()
        
        input_path = filedialog.askopenfilename(title="Dönüştürülecek Dosyayı Seçin")
        if not input_path:
            return
            
        target_path = filedialog.askdirectory(title="Çıktı Nereye Kaydedilsin?")
        if not target_path:
            return
        
        self.update_ui(self.conv_btn, state="disabled")
        self.update_ui(self.conv_status, text="Dönüştürme başlatılıyor...", text_color="white")
        self.conv_progress.set(0)

        threading.Thread(target=self._process_conversion, args=(input_path, target_format, target_path), daemon=True).start()

    def _process_conversion(self, input_path, target_format, target_dir):
        try:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(target_dir, f"{base_name}_converted.{target_format}")
            
            img_formats = ["png", "webp", "ico"]
            vid_aud_formats = ["mp3", "mp4"]

            if target_format in img_formats:
                self.update_ui(self.conv_status, text="Görsel işleniyor...", text_color="white")
                self.update_progress(self.conv_progress, 0.5)
                
                img = Image.open(input_path)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGBA")
                elif target_format != "png":
                    img = img.convert("RGB")

                if target_format == "ico":
                    img.save(output_path, format="ICO", sizes=[(256, 256)])
                else:
                    img.save(output_path, format=target_format.upper())
                
                self.update_progress(self.conv_progress, 1.0)

            elif target_format in vid_aud_formats:
                self.update_ui(self.conv_status, text="Medya dosyası okunuyor, bu işlem dosya boyutuna göre biraz sürebilir...", text_color="yellow")
                self.update_progress(self.conv_progress, 0.3) 
                
                if target_format == "mp3":
                    clip = AudioFileClip(input_path)
                    self.update_ui(self.conv_status, text="Ses dosyası dışa aktarılıyor...", text_color="yellow")
                    self.update_progress(self.conv_progress, 0.6)
                    clip.write_audiofile(output_path, logger=None)
                    clip.close()
                
                elif target_format == "mp4":
                    clip = VideoFileClip(input_path)
                    self.update_ui(self.conv_status, text="Video dosyası dışa aktarılıyor...", text_color="yellow")
                    self.update_progress(self.conv_progress, 0.6)
                    clip.write_videofile(output_path, logger=None)
                    clip.close()

                self.update_progress(self.conv_progress, 1.0)

            self.update_ui(self.conv_status, text="İşlem Bitti! Dosya başarıyla oluşturuldu.", text_color="#00FF00")
        
        except Exception as e:
            self.update_ui(self.conv_status, text="Dönüştürme Hatası! (Format uyumsuz olabilir)", text_color="red")
            print(f"Hata detayı: {e}")
        finally:
            self.update_ui(self.conv_btn, state="normal")

if __name__ == "__main__":
    app = ZoyMediaTool()
    app.mainloop()
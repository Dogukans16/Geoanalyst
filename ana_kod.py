import threading
import json
import keyboard
import pyautogui
import win32clipboard
import customtkinter as ctk
import tkintermapview
from PIL import Image
import time
import requests
import base64
from io import BytesIO

# !!! DİKKAT: KOPYALADIĞIN SUPABASE EDGE FUNCTION URL'Nİ BURAYA YAPIŞTIR !!!
SUPABASE_FUNCTION_URL = "https://dkmwtyncxxmgotepgjxr.supabase.co/functions/v1/analizyap"

class KonumAsistani(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PENCERE AYARLARI ---
        self.title("Konum Asistanı")
        self.geometry("400x750") # Telefon gibi dikey ve dikdörtgen
        self.resizable(False, False)
        
        # Varsayılan ayarlar ve Değişkenler
        self.guncel_tus = "8"
        self.analiz_yapiliyor = False  # Aynı anda birden fazla istek gitmesini önleyen kilit
        self.kullanici_eposta = ""     # Giriş yapan kullanıcının e-postası

        # Uygulama açıldığında önce giriş ekranını göster
        self.giris_ekrani_olustur()

    def giris_ekrani_olustur(self):
        """Kullanıcıdan e-posta alan giriş ekranı"""
        self.giris_frame = ctk.CTkFrame(self)
        self.giris_frame.pack(pady=200, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.giris_frame, text="Sisteme Giriş", font=("Arial", 24, "bold")).pack(pady=20)
        
        self.eposta_giris = ctk.CTkEntry(self.giris_frame, placeholder_text="Kayıtlı E-posta adresiniz", width=250)
        self.eposta_giris.pack(pady=10)

        giris_btn = ctk.CTkButton(self.giris_frame, text="Giriş Yap", command=self.giris_yap)
        giris_btn.pack(pady=20)

        self.giris_hata_etiket = ctk.CTkLabel(self.giris_frame, text="", text_color="red")
        self.giris_hata_etiket.pack(pady=5)

    def giris_yap(self):
        eposta = self.eposta_giris.get().strip()
        if "@" in eposta:
            self.kullanici_eposta = eposta
            self.giris_frame.pack_forget()  # Giriş ekranını gizle
            self.arayuzu_olustur()          # Ana harita arayüzünü yükle
            self.kisayolu_guncelle(self.guncel_tus)
        else:
            self.giris_hata_etiket.configure(text="Lütfen geçerli bir e-posta girin!")

    def arayuzu_olustur(self):
        """Ana Harita ve Navigasyon Arayüzü"""
        # Aktif Kullanıcı Bilgisi (En Üstte)
        ctk.CTkLabel(self, text=f"👤 Giriş yapıldı: {self.kullanici_eposta}", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(10,0))

        # 1. ÜST PANEL: AYARLAR (Tuş Atama)
        self.ayar_frame = ctk.CTkFrame(self)
        self.ayar_frame.pack(pady=10, padx=10, fill="x")

        self.ayar_etiket = ctk.CTkLabel(self.ayar_frame, text="Kısayol Tuşu:", font=("Arial", 14, "bold"))
        self.ayar_etiket.pack(side="left", padx=10, pady=10)

        self.tus_giris = ctk.CTkEntry(self.ayar_frame, width=50)
        self.tus_giris.insert(0, self.guncel_tus)
        self.tus_giris.pack(side="left", padx=5)

        self.kaydet_buton = ctk.CTkButton(self.ayar_frame, text="Kaydet", width=80, command=self.ayarlari_kaydet)
        self.kaydet_buton.pack(side="left", padx=5)

        # 2. ORTA PANEL: NAVİGASYON (Gömülü Harita)
        self.harita_frame = ctk.CTkFrame(self)
        self.harita_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.harita = tkintermapview.TkinterMapView(self.harita_frame, corner_radius=10)
        self.harita.pack(fill="both", expand=True)
        
        # Google Haritalar Sunucusu
        self.harita.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=tr&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        
        self.harita.set_position(39.92077, 32.85411) # Varsayılan Ankara
        self.harita.set_zoom(5)

        # 3. ALT BİLGİ PANELİ: (Ülke, Şehir, Koordinat)
        self.bilgi_frame = ctk.CTkFrame(self)
        self.bilgi_frame.pack(pady=5, padx=10, fill="x")

        self.konum_etiket = ctk.CTkLabel(self.bilgi_frame, text="Konum: Bekleniyor...", font=("Arial", 16, "bold"), text_color="#1f6aa5")
        self.konum_etiket.pack(pady=5)

        self.koordinat_etiket = ctk.CTkLabel(self.bilgi_frame, text="Koordinatlar: Bekleniyor...", font=("Arial", 12))
        self.koordinat_etiket.pack(pady=5)

        self.durum_etiket = ctk.CTkLabel(self.bilgi_frame, text="🟢 Sistem Hazır. Oyundayken tuşa bas.", font=("Arial", 12, "italic"), text_color="#2ecc71")
        self.durum_etiket.pack(pady=5)

        # 4. EN ALT PANEL: TEMA AYARLARI
        self.tema_frame = ctk.CTkFrame(self)
        self.tema_frame.pack(pady=10, padx=10, fill="x")

        self.tema_switch = ctk.CTkSwitch(self.tema_frame, text="Karanlık Mod", command=self.tema_degistir)
        self.tema_switch.pack(side="left", padx=20, pady=10)
        self.tema_switch.select() 

        self.renk_buton = ctk.CTkButton(self.tema_frame, text="Yeşil Tema", width=100, command=lambda: ctk.set_default_color_theme("green"))
        self.renk_buton.pack(side="right", padx=20)

    def ayarlari_kaydet(self):
        yeni_tus = self.tus_giris.get().lower()
        if yeni_tus:
            self.kisayolu_guncelle(yeni_tus)
            self.durum_guncelle(f"ℹ️ Kısayol '{yeni_tus}' olarak güncellendi.", "#1f6aa5")

    def kisayolu_guncelle(self, yeni_tus):
        try:
            keyboard.unhook_all() 
            self.guncel_tus = yeni_tus
            keyboard.add_hotkey(self.guncel_tus, lambda: threading.Thread(target=self.analiz_baslat).start())
        except Exception as e:
            self.durum_guncelle(f"❌ Tuş atama hatası: {e}", "#e74c3c")

    def tema_degistir(self):
        if self.tema_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def durum_guncelle(self, mesaj, renk="#ffffff"):
        if getattr(self, "tema_switch", None) and self.tema_switch.get() == 0 and renk == "#ffffff":
            renk = "#000000"
        self.after(0, lambda: self.durum_etiket.configure(text=mesaj, text_color=renk))

    def analiz_baslat(self):
        # KRİTİK KONTROL: Eğer zaten bir analiz çalışıyorsa bu basışı görmezden gel!
        if self.analiz_yapiliyor:
            return
        
        # Sistemi kilitle
        self.analiz_yapiliyor = True
        self.durum_guncelle("⌨️ Tuş algılandı! İşlem başlatılıyor...", "#f1c40f")
        
        try:
            self.durum_guncelle("📸 Ekran görüntüsü yakalanıyor...", "#f1c40f")
            ekran = pyautogui.screenshot()
            
            # Görsel boyutunu küçülterek hızı optimize ediyoruz
            ekran.thumbnail((1024, 1024)) 

            # Görseli Base64 formatına çevirme (İnternet üzerinden göndermek için)
            buffered = BytesIO()
            ekran.save(buffered, format="JPEG")
            gorsel_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            self.durum_guncelle("🧠 Kredi kontrol ediliyor ve Analiz yapılıyor...", "#3498db")
            
            prompt = """
            Bu oyun ekran görüntüsündeki yer neresi? 
            Bana SADECE aşağıdaki formatta geçerli bir JSON çıktısı ver. Başka hiçbir kelime veya markdown karakteri (json gibi) kullanma:
            {"ulke": "Ülke Adı", "sehir": "Şehir/İlçe Adı", "enlem": 41.0082, "boylam": 28.9784}
            Eğer tam koordinat bulamazsan tahmini bir koordinat ver.
            """
            
            # SUPABASE SUNUCUMUZA GÜVENLİ İSTEK ATIYORUZ
            payload = {
                "eposta": self.kullanici_eposta,
                "prompt": prompt,
                "gorsel_base64": gorsel_base64
            }
            
            response = requests.post(SUPABASE_FUNCTION_URL, json=payload)
            cevap_json = response.json()

            # Cevap başarılıysa (Kredi var ve analiz yapıldıysa)
            if response.status_code == 200:
                # Gemini'nin döndürdüğü karmaşık JSON yapısından sadece metin kısmını alıyoruz
                metin_cevap = cevap_json["sonuc"]["candidates"][0]["content"]["parts"][0]["text"]
                ham_cevap = metin_cevap.strip().replace("json", "").replace("```", "")
                veri = json.loads(ham_cevap)

                ulke = veri.get("ulke", "Bilinmiyor")
                sehir = veri.get("sehir", "Bilinmiyor")
                enlem = float(veri.get("enlem", 0.0))
                boylam = float(veri.get("boylam", 0.0))

                self.after(0, self.ekrani_guncelle, ulke, sehir, enlem, boylam)

                kopyalanacak_metin = f"{enlem}, {boylam}"
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, kopyalanacak_metin)
                win32clipboard.CloseClipboard()
                
                # Başarılıysa kilidi açmadan önce 3 saniye soğuma süresi (cooldown) veriyoruz
                threading.Timer(3.0, self.kilidi_ac).start()

            # Kredi bitmişse
            elif response.status_code == 403:
                self.durum_guncelle("❌ Krediniz bitti. Lütfen yenileyin.", "#e74c3c")
                threading.Timer(3.0, self.kilidi_ac_hata).start()

            # Kullanıcı bulunamadıysa veya e-posta yanlışsa
            elif response.status_code == 400:
                self.durum_guncelle("❌ Kayıtlı kullanıcı bulunamadı!", "#e74c3c")
                threading.Timer(3.0, self.kilidi_ac_hata).start()
                
            # Diğer hatalar
            else:
                self.durum_guncelle(f"❌ Sunucu Hatası: {cevap_json.get('hata', 'Bilinmeyen hata')}", "#e74c3c")
                threading.Timer(3.0, self.kilidi_ac_hata).start()

        except Exception as e:
            self.durum_guncelle("❌ Hata oluştu! 5 saniye sonra tekrar dene.", "#e74c3c")
            print(f"HATA Detayı: {e}")
            threading.Timer(5.0, self.kilidi_ac_hata).start()

    def kilidi_ac(self):
        self.analiz_yapiliyor = False
        self.durum_guncelle("🟢 Sistem Hazır. Oyundayken tuşa bas.", "#2ecc71")

    def kilidi_ac_hata(self):
        self.analiz_yapiliyor = False
        self.durum_guncelle("🟢 Sistem Hazır. Tekrar deneyebilirsiniz.", "#2ecc71")

    def ekrani_guncelle(self, ulke, sehir, enlem, boylam):
        self.konum_etiket.configure(text=f"{ulke}, {sehir}")
        self.koordinat_etiket.configure(text=f"Koordinat: {enlem}, {boylam}")
        
        self.harita.set_position(enlem, boylam)
        self.harita.set_zoom(10) 
        self.harita.delete_all_marker()
        self.harita.set_marker(enlem, boylam, text=sehir)
        
        self.durum_guncelle("⏳ Tamamlandı! Koruma kilidi devrede...", "#e67e22")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  
    ctk.set_default_color_theme("blue")  

    uygulama = KonumAsistani()
    uygulama.mainloop()
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

# --- AYARLAR VE BAĞLANTI ---
SUPABASE_FUNCTION_URL = "https://dkmwtyncxxmgotepgjxr.supabase.co/functions/v1/analizyap"
GITHUB_KOD_URL = "https://raw.githubusercontent.com/KULLANICI_ADIN/konum-asistani/main/ana_kod.py" # İleride güncelleme için kullanacaksın

class KonumAsistani(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PENCERE AYARLARI ---
        self.title("Konum Asistanı Pro")
        self.geometry("420x780")
        self.resizable(False, False)
        
        # Değişkenler
        self.guncel_tus = "8"
        self.analiz_yapiliyor = False
        self.kullanici_eposta = ""
        self.kullanici_sifre = ""
        self.mevcut_tema_rengi = "#1f6aa5" # Varsayılan mavi tema rengi

        # İlk olarak giriş/kayıt ekranını başlat
        self.giris_ekrani_olustur()

    def giris_ekrani_olustur(self):
        """Şık Çerçeveli Giriş ve Kayıt Ekranı"""
        self.giris_frame = ctk.CTkFrame(self, border_width=2, border_color=self.mevcut_tema_rengi)
        self.giris_frame.pack(pady=120, padx=30, fill="both", expand=True)

        self.giris_baslik = ctk.CTkLabel(self.giris_frame, text="MÜŞTERİ PANELİ", font=("Arial", 22, "bold"))
        self.giris_baslik.pack(pady=(30, 20))
        
        self.eposta_giris = ctk.CTkEntry(self.giris_frame, placeholder_text="E-posta Adresiniz", width=260)
        self.eposta_giris.pack(pady=10)

        self.sifre_giris = ctk.CTkEntry(self.giris_frame, placeholder_text="Şifreniz", show="*", width=260)
        self.sifre_giris.pack(pady=10)

        # Butonlar için yan yana düzen
        btn_frame = ctk.CTkFrame(self.giris_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        giris_btn = ctk.CTkButton(btn_frame, text="Giriş Yap", width=120, fg_color=self.mevcut_tema_rengi, command=self.giris_yap)
        giris_btn.pack(side="left", padx=5)

        kayit_btn = ctk.CTkButton(btn_frame, text="Kayıt Ol (Demo)", width=120, fg_color="#2ecc71", command=self.kayit_ol)
        kayit_btn.pack(side="left", padx=5)

        self.giris_durum_etiket = ctk.CTkLabel(self.giris_frame, text="", font=("Arial", 12, "bold"))
        self.giris_durum_etiket.pack(pady=10)

    def giris_yap(self):
        eposta = self.eposta_giris.get().strip()
        sifre = self.sifre_giris.get().strip()

        if not eposta or not sifre or "@" not in eposta:
            self.giris_durum_etiket.configure(text="❌ Geçerli e-posta ve şifre girin!", text_color="#e74c3c")
            return

        self.giris_durum_etiket.configure(text="🔒 Doğrulanıyor...", text_color="#f1c40f")
        
        # Sunucuya giriş isteği gönderiyoruz
        threading.Thread(target=self.sunucu_giris_kontrol, args=(eposta, sifre)).start()

    def sunucu_giris_kontrol(self, eposta, sifre):
        try:
            payload = {"islem": "giris", "eposta": eposta, "sifre": sifre}
            response = requests.post(SUPABASE_FUNCTION_URL, json=payload)
            cevap = response.json()

            if response.status_code == 200:
                self.kullanici_eposta = eposta
                self.kullanici_sifre = sifre
                abonelik = cevap.get("abonelik_tipi", "demo").upper()
                kredi = cevap.get("kalan_kredi", 0)
                
                # Giriş başarılı arayüze geç
                self.after(0, self.ana_ekrana_gec, abonelik, kredi)
            else:
                self.after(0, lambda: self.giris_durum_etiket.configure(text=f"❌ {cevap.get('hata', 'Hata oluştu')}", text_color="#e74c3c"))
        except Exception as e:
            self.after(0, lambda: self.giris_durum_etiket.configure(text="❌ Sunucu bağlantı hatası!", text_color="#e74c3c"))

    def kayit_ol(self):
        eposta = self.eposta_giris.get().strip()
        sifre = self.sifre_giris.get().strip()

        if not eposta or not sifre or "@" not in eposta:
            self.giris_durum_etiket.configure(text="❌ Kayıt için geçerli e-posta ve şifre yazın!", text_color="#e74c3c")
            return

        # Spam/Geçici E-posta Koruması
        yasakli_uzantilar = ["tempmail.com", "mailinator.com", "yopmail.com", "sharklasers.com", "guerrillamail.com"]
        uzanti = eposta.split("@")[-1].lower()
        if uzanti in yasakli_uzantilar:
            self.giris_durum_etiket.configure(text="❌ Spam e-posta adresleri yasaktır!", text_color="#e74c3c")
            return

        self.giris_durum_etiket.configure(text="📝 Kayıt yapılıyor...", text_color="#f1c40f")
        threading.Thread(target=self.sunucu_kayit_islemi, args=(eposta, sifre)).start()

    def sunucu_kayit_islemi(self, eposta, sifre):
        try:
            payload = {"islem": "kayit", "eposta": eposta, "sifre": sifre}
            response = requests.post(SUPABASE_FUNCTION_URL, json=payload)
            cevap = response.json()

            if response.status_code == 200:
                self.after(0, lambda: self.giris_durum_etiket.configure(text="✅ Kayıt Başarılı! Giriş Yapabilirsiniz.", text_color="#2ecc71"))
            else:
                self.after(0, lambda: self.giris_durum_etiket.configure(text=f"❌ {cevap.get('hata', 'Kayıt başarısız')}", text_color="#e74c3c"))
        except Exception as e:
            self.after(0, lambda: self.giris_durum_etiket.configure(text="❌ Sunucu bağlantı hatası!", text_color="#e74c3c"))

    def ana_ekrana_gec(self, abonelik, kredi):
        self.giris_frame.pack_forget()
        self.arayuzu_olustur(abonelik, kredi)
        self.kisayolu_guncelle(self.guncel_tus)

    def arayuzu_olustur(self, abonelik, kredi):
        """Renkli Çerçeveli Gelişmiş Harita Ekranı"""
        # Üst Bilgi Satırı
        ctk.CTkLabel(self, text=f"👤 {self.kullanici_eposta}", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(10,0))

        # 1. ÜST PANEL: AYARLAR (Tuş Atama)
        self.ayar_frame = ctk.CTkFrame(self, border_width=1, border_color=self.mevcut_tema_rengi)
        self.ayar_frame.pack(pady=5, padx=15, fill="x")

        ctk.CTkLabel(self.ayar_frame, text="Kısayol Tuşu:", font=("Arial", 13, "bold")).pack(side="left", padx=10, pady=10)
        self.tus_giris = ctk.CTkEntry(self.ayar_frame, width=40)
        self.tus_giris.insert(0, self.guncel_tus)
        self.tus_giris.pack(side="left", padx=5)

        self.kaydet_buton = ctk.CTkButton(self.ayar_frame, text="Kaydet", width=60, fg_color=self.mevcut_tema_rengi, command=self.ayarlari_kaydet)
        self.kaydet_buton.pack(side="left", padx=5)

        # 2. ORTA PANEL: HARİTA
        self.harita_frame = ctk.CTkFrame(self, border_width=2, border_color=self.mevcut_tema_rengi)
        self.harita_frame.pack(pady=5, padx=15, fill="both", expand=True)
        
        self.harita = tkintermapview.TkinterMapView(self.harita_frame, corner_radius=10)
        self.harita.pack(fill="both", expand=True, padx=2, pady=2)
        self.harita.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=tr&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        self.harita.set_position(39.92077, 32.85411) # Ankara
        self.harita.set_zoom(5)

        # 3. ALT BİLGİ PANELİ (Konum, Koordinat, Üyelik Tipi ve Kalan Kredi)
        self.bilgi_frame = ctk.CTkFrame(self, border_width=1, border_color=self.mevcut_tema_rengi)
        self.bilgi_frame.pack(pady=5, padx=15, fill="x")

        self.konum_etiket = ctk.CTkLabel(self.bilgi_frame, text="Konum: Bekleniyor...", font=("Arial", 15, "bold"), text_color=self.mevcut_tema_rengi)
        self.konum_etiket.pack(pady=3)

        self.koordinat_etiket = ctk.CTkLabel(self.bilgi_frame, text="Koordinat: - , -", font=("Arial", 12))
        self.koordinat_etiket.pack(pady=2)

        # 5 Farklı Üyelik Tipi ve Dinamik Kredi Göstergesi
        kredi_yazisi = "Sınırsız Kredi" if abonelik == "ADMIN" else f"{kredi} Hak Kaldı"
        self.kredi_etiket = ctk.CTkLabel(self.bilgi_frame, text=f"👑 VIP: {abonelik} | 📊 {kredi_yazisi}", font=("Arial", 11, "bold"), text_color="#e67e22")
        self.kredi_etiket.pack(pady=2)

        self.durum_etiket = ctk.CTkLabel(self.bilgi_frame, text="🟢 Sistem Hazır. Oyundayken tuşa bas.", font=("Arial", 12, "italic"), text_color="#2ecc71")
        self.durum_etiket.pack(pady=5)

        # 4. EN ALT PANEL: TEMA VE DİNAMİK RENK DEĞİŞTİRME MENÜSÜ
        self.renk_frame = ctk.CTkFrame(self, border_width=1, border_color=self.mevcut_tema_rengi)
        self.renk_frame.pack(pady=(5, 15), padx=15, fill="x")

        ctk.CTkLabel(self.renk_frame, text="Arayüz Rengi:", font=("Arial", 11, "bold")).pack(side="left", padx=10, pady=10)
        
        # Kullanıcının menü rengini değiştirebileceği seçenekler
        self.renk_secimi = ctk.CTkOptionMenu(
            self.renk_frame, 
            values=["Mavi", "Yeşil", "Kırmızı", "Mor", "Turuncu"], 
            width=120,
            fg_color=self.mevcut_tema_rengi,
            button_color=self.mevcut_tema_rengi,
            command=self.arayuz_rengini_degistir
        )
        self.renk_secimi.pack(side="right", padx=10)

    def arayuz_rengini_degistir(self, secilen_renk):
        renk_haritasi = {
            "Mavi": "#1f6aa5",
            "Yeşil": "#2ecc71",
            "Kırmızı": "#e74c3c",
            "Mor": "#9b59b6",
            "Turuncu": "#e67e22"
        }
        self.mevcut_tema_rengi = renk_haritasi.get(secilen_renk, "#1f6aa5")
        
        # Çerçeve ve Etiket Renklerini Canlı Güncelle
        self.ayar_frame.configure(border_color=self.mevcut_tema_rengi)
        self.harita_frame.configure(border_color=self.mevcut_tema_rengi)
        self.bilgi_frame.configure(border_color=self.mevcut_tema_rengi)
        self.renk_frame.configure(border_color=self.mevcut_tema_rengi)
        self.konum_etiket.configure(text_color=self.mevcut_tema_rengi)
        self.renk_secimi.configure(fg_color=self.mevcut_tema_rengi, button_color=self.mevcut_tema_rengi)

    def ayarlari_kaydet(self):
        yeni_tus = self.tus_giris.get().lower()
        if yeni_tus:
            self.kisayolu_guncelle(yeni_tus)
            self.durum_guncelle(f"ℹ️ Kısayol '{yeni_tus}' yapıldı.", self.mevcut_tema_rengi)

    def kisayolu_guncelle(self, yeni_tus):
        try:
            keyboard.unhook_all() 
            self.guncel_tus = yeni_tus
            keyboard.add_hotkey(self.guncel_tus, lambda: threading.Thread(target=self.analiz_baslat).start())
        except Exception as e:
            self.durum_guncelle(f"❌ Tuş hatası: {e}", "#e74c3c")

    def durum_guncelle(self, mesaj, renk="#ffffff"):
        self.after(0, lambda: self.durum_etiket.configure(text=mesaj, text_color=renk))

    def analiz_baslat(self):
        if self.analiz_yapiliyor: return
        self.analiz_yapiliyor = True
        
        self.durum_guncelle("📸 Ekran taranıyor...", "#f1c40f")
        
        try:
            ekran = pyautogui.screenshot()
            ekran.thumbnail((1024, 1024)) 

            buffered = BytesIO()
            ekran.save(buffered, format="JPEG")
            gorsel_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            self.durum_guncelle("🧠 Analiz ediliyor...", "#3498db")
            
            prompt = """
            Bu oyun ekran görüntüsündeki yer neresi? 
            Bana SADECE aşağıdaki formatta geçerli bir JSON çıktısı ver. Başka hiçbir kelime veya markdown karakteri kullanma:
            {"ulke": "Ülke Adı", "sehir": "Şehir Adı", "enlem": 41.0082, "boylam": 28.9784}
            """
            
            payload = {
                "islem": "analiz",
                "eposta": self.kullanici_eposta,
                "prompt": prompt,
                "gorsel_base64": gorsel_base64
            }
            
            response = requests.post(SUPABASE_FUNCTION_URL, json=payload)
            cevap_json = response.json()

            if response.status_code == 200:
                metin_cevap = cevap_json["sonuc"]["candidates"][0]["content"]["parts"][0]["text"]
                ham_cevap = metin_cevap.strip().replace("json", "").replace("```", "")
                veri = json.loads(ham_cevap)

                ulke = veri.get("ulke", "Bilinmiyor")
                sehir = veri.get("sehir", "Bilinmiyor")
                enlem = float(veri.get("enlem", 0.0))
                boylam = float(veri.get("boylam", 0.0))

                # Haritayı ve kalan kredi miktarını anlık güncelle
                yeni_kredi = cevap_json.get("kalan_kredi", 0)
                self.after(0, self.ekrani_guncelle, ulke, sehir, enlem, boylam, yeni_kredi)

                # Koordinatları kopyala
                kopyalanacak_metin = f"{enlem}, {boylam}"
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, kopyalanacak_metin)
                win32clipboard.CloseClipboard()
                
                threading.Timer(2.0, self.kilidi_ac).start()

            elif response.status_code == 403:
                self.durum_guncelle("❌ Krediniz bitti! Paketi yenileyin.", "#e74c3c")
                threading.Timer(3.0, self.kilidi_ac).start()
            else:
                self.durum_guncelle(f"❌ Hata: {cevap_json.get('hata', 'Bilinmiyor')}", "#e74c3c")
                threading.Timer(3.0, self.kilidi_ac).start()

        except Exception as e:
            self.durum_guncelle("❌ Sistem Hatası!", "#e74c3c")
            threading.Timer(3.0, self.kilidi_ac).start()

    def kilidi_ac(self):
        self.analiz_yapiliyor = False
        self.durum_guncelle("🟢 Sistem Hazır. Oyundayken tuşa bas.", "#2ecc71")

    def ekrani_guncelle(self, ulke, sehir, enlem, boylam, yeni_kredi):
        self.konum_etiket.configure(text=f"{ulke}, {sehir}")
        self.koordinat_etiket.configure(text=f"Koordinat: {enlem}, {boylam}")
        
        # Eğer kullanıcı admin değilse kalan krediyi düşürerek ekranda göster
        if "Sınırsız" not in self.kredi_etiket.cget("text"):
            self.kredi_etiket.configure(text=f"👑 VIP: AKTİF | 📊 {yeni_kredi} Hak Kaldı")

        self.harita.set_position(enlem, boylam)
        self.harita.set_zoom(11) 
        self.harita.delete_all_marker()
        self.harita.set_marker(enlem, boylam, text=sehir)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  
    uygulama = KonumAsistani()
    uygulama.mainloop()
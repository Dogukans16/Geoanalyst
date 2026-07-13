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
import webbrowser
from io import BytesIO
import sys
import os

# --- AYARLAR ---
SUPABASE_FUNCTION_URL = "https://dkmwtyncxxmgotepgjxr.supabase.co/functions/v1/analizyap"
# Kendi GitHub kullanıcı adını buraya yaz:
VERSION_URL = "https://raw.githubusercontent.com/KULLANICI_ADIN/konum-asistani/main/surum.txt"
EXE_DOWNLOAD_URL = "https://github.com/KULLANICI_ADIN/konum-asistani/releases/latest"
GUNCEL_SURUM = "1.1.0"

class Geoanalyst(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PENCERE AYARLARI (ŞAHİN GÖZÜ TASARIMI) ---
        self.title("Geoanalyst | Şahin Gözü")
        self.geometry("420x780")
        self.resizable(False, False)
        
        # Tema Renkleri
        self.tema_rengi = "#f1c40f" # Şahin Gözü Sarısı
        self.arka_plan = "#2c3e50" # Koyu Karbon
        
        self.guncel_tus = "8"
        self.analiz_yapiliyor = False
        self.kullanici_eposta = ""

        # Arayüzü Başlat
        self.giris_ekrani_olustur()
        
        # Güncelleme Kontrolünü Başlat
        threading.Thread(target=self.guncelleme_kontrol_et, daemon=True).start()

    # --- GÜNCELLEME SİSTEMİ ---
    def guncelleme_kontrol_et(self):
        try:
            response = requests.get(VERSION_URL, timeout=5)
            github_surum = response.text.strip()
            if github_surum != GUNCEL_SURUM:
                self.after(0, self.guncelleme_uyarisi_goster)
        except:
            pass

    def guncelleme_uyarisi_goster(self):
        self.guncelleme_btn = ctk.CTkButton(self, text="🚀 Yeni Sürüm Var! Tıkla İndir", fg_color="#e67e22", command=lambda: webbrowser.open(EXE_DOWNLOAD_URL))
        self.guncelleme_btn.pack(pady=5, padx=20, fill="x")

    # --- GİRİŞ VE KAYIT ---
    def giris_ekrani_olustur(self):
        self.giris_frame = ctk.CTkFrame(self, border_width=2, border_color=self.tema_rengi)
        self.giris_frame.pack(pady=100, padx=30, fill="both", expand=True)

        ctk.CTkLabel(self.giris_frame, text="👁️ GEOANALYST", font=("Arial", 24, "bold"), text_color=self.tema_rengi).pack(pady=(30, 20))
        
        self.eposta_giris = ctk.CTkEntry(self.giris_frame, placeholder_text="E-posta", width=260)
        self.eposta_giris.pack(pady=10)

        self.sifre_giris = ctk.CTkEntry(self.giris_frame, placeholder_text="Şifre", show="*", width=260)
        self.sifre_giris.pack(pady=10)

        btn_frame = ctk.CTkFrame(self.giris_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Giriş Yap", width=120, fg_color=self.tema_rengi, text_color="black", command=self.giris_yap).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Kayıt Ol", width=120, fg_color="#2ecc71", command=self.kayit_ol).pack(side="left", padx=5)

        self.giris_durum_etiket = ctk.CTkLabel(self.giris_frame, text="", font=("Arial", 12, "bold"))
        self.giris_durum_etiket.pack(pady=10)

    def giris_yap(self):
        eposta = self.eposta_giris.get().strip()
        sifre = self.sifre_giris.get().strip()
        if not eposta or not sifre: return
        self.giris_durum_etiket.configure(text="🔍 Odaklanılıyor...", text_color=self.tema_rengi)
        threading.Thread(target=self.sunucu_giris_kontrol, args=(eposta, sifre), daemon=True).start()

    def sunucu_giris_kontrol(self, eposta, sifre):
        try:
            response = requests.post(SUPABASE_FUNCTION_URL, json={"islem": "giris", "eposta": eposta, "sifre": sifre})
            cevap = response.json()
            if response.status_code == 200:
                self.kullanici_eposta = eposta
                self.after(0, self.ana_ekrana_gec, cevap.get("abonelik_tipi", "demo").upper(), cevap.get("kalan_kredi", 0))
            else:
                self.after(0, lambda: self.giris_durum_etiket.configure(text=f"❌ Hata", text_color="#e74c3c"))
        except:
            self.after(0, lambda: self.giris_durum_etiket.configure(text="❌ Bağlantı Hatası!", text_color="#e74c3c"))

    def kayit_ol(self):
        eposta = self.eposta_giris.get().strip()
        sifre = self.sifre_giris.get().strip()
        if not eposta or not sifre: return
        self.giris_durum_etiket.configure(text="📝 Kayıt yapılıyor...", text_color=self.tema_rengi)
        threading.Thread(target=self.sunucu_kayit_islemi, args=(eposta, sifre), daemon=True).start()

    def sunucu_kayit_islemi(self, eposta, sifre):
        try:
            response = requests.post(SUPABASE_FUNCTION_URL, json={"islem": "kayit", "eposta": eposta, "sifre": sifre})
            if response.status_code == 200:
                self.after(0, lambda: self.giris_durum_etiket.configure(text="✅ Kayıt Başarılı!", text_color="#2ecc71"))
            else:
                self.after(0, lambda: self.giris_durum_etiket.configure(text=f"❌ Hata", text_color="#e74c3c"))
        except:
            self.after(0, lambda: self.giris_durum_etiket.configure(text="❌ Bağlantı Hatası!", text_color="#e74c3c"))

    # --- ANA EKRAN ---
    def ana_ekrana_gec(self, abonelik, kredi):
        self.giris_frame.pack_forget()
        self.arayuzu_olustur(abonelik, kredi)
        self.kisayolu_guncelle(self.guncel_tus)

    def arayuzu_olustur(self, abonelik, kredi):
        ctk.CTkLabel(self, text=f"👤 {self.kullanici_eposta}", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(10,0))
        self.ayar_frame = ctk.CTkFrame(self, border_width=1, border_color=self.tema_rengi)
        self.ayar_frame.pack(pady=5, padx=15, fill="x")
        self.tus_giris = ctk.CTkEntry(self.ayar_frame, width=40)
        self.tus_giris.insert(0, self.guncel_tus)
        self.tus_giris.pack(side="left", padx=10, pady=10)
        ctk.CTkButton(self.ayar_frame, text="Kısayol Kaydet", width=100, fg_color=self.tema_rengi, text_color="black", command=self.ayarlari_kaydet).pack(side="left", padx=5)

        self.harita_frame = ctk.CTkFrame(self, border_width=2, border_color=self.tema_rengi)
        self.harita_frame.pack(pady=5, padx=15, fill="both", expand=True)
        self.harita = tkintermapview.TkinterMapView(self.harita_frame, corner_radius=10)
        self.harita.pack(fill="both", expand=True, padx=2, pady=2)
        self.harita.set_position(39.92077, 32.85411)
        self.harita.set_zoom(5)

        self.bilgi_frame = ctk.CTkFrame(self, border_width=1, border_color=self.tema_rengi)
        self.bilgi_frame.pack(pady=5, padx=15, fill="x")
        self.konum_etiket = ctk.CTkLabel(self.bilgi_frame, text="🎯 Şahin Hazır", font=("Arial", 15, "bold"), text_color=self.tema_rengi)
        self.konum_etiket.pack(pady=3)
        self.koordinat_etiket = ctk.CTkLabel(self.bilgi_frame, text="Koordinat: Bekleniyor", font=("Arial", 12))
        self.koordinat_etiket.pack(pady=2)
        kredi_yazisi = "Sınırsız" if abonelik == "ADMIN" else f"{kredi} Hak"
        self.kredi_etiket = ctk.CTkLabel(self.bilgi_frame, text=f"👑 VIP: {abonelik} | 📊 {kredi_yazisi}", font=("Arial", 11, "bold"), text_color=self.tema_rengi)
        self.kredi_etiket.pack(pady=2)
        self.durum_etiket = ctk.CTkLabel(self.bilgi_frame, text="👁️ Gözlem Başlat", font=("Arial", 12, "italic"), text_color="#2ecc71")
        self.durum_etiket.pack(pady=5)

    def ayarlari_kaydet(self):
        yeni_tus = self.tus_giris.get().lower()
        if yeni_tus:
            self.kisayolu_guncelle(yeni_tus)
            self.durum_guncelle(f"ℹ️ Şahin tetik tuşu: '{yeni_tus}'", self.tema_rengi)

    def kisayolu_guncelle(self, yeni_tus):
        keyboard.unhook_all()
        self.guncel_tus = yeni_tus
        keyboard.add_hotkey(self.guncel_tus, lambda: threading.Thread(target=self.analiz_baslat, daemon=True).start())

    def durum_guncelle(self, mesaj, renk="#ffffff"):
        self.after(0, lambda: self.durum_etiket.configure(text=mesaj, text_color=renk))

    def analiz_baslat(self):
        if self.analiz_yapiliyor: return
        self.analiz_yapiliyor = True
        self.durum_guncelle("📸 Şahin odaklanıyor...", "#f1c40f")
        try:
            ekran = pyautogui.screenshot()
            ekran.thumbnail((1024, 1024))
            buffered = BytesIO()
            ekran.save(buffered, format="JPEG")
            gorsel_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            response = requests.post(SUPABASE_FUNCTION_URL, json={
                "islem": "analiz", "eposta": self.kullanici_eposta,
                "prompt": "Yer neresi? JSON formatında: {'ulke': '...', 'sehir': '...', 'enlem': 0, 'boylam': 0}",
                "gorsel_base64": gorsel_base64
            })
            
            if response.status_code == 200:
                cevap = response.json()
                veri = json.loads(cevap["sonuc"]["candidates"][0]["content"]["parts"][0]["text"].replace("```json", "").replace("```", "").strip())
                self.after(0, self.ekrani_guncelle, veri.get("ulke"), veri.get("sehir"), veri.get("enlem"), veri.get("boylam"), cevap.get("kalan_kredi"))
                self.kilidi_ac()
            else:
                self.durum_guncelle("❌ Hata oluştu!", "#e74c3c")
                self.kilidi_ac()
        except:
            self.durum_guncelle("❌ Sistem Hatası!", "#e74c3c")
            self.kilidi_ac()

    def kilidi_ac(self):
        self.analiz_yapiliyor = False
        self.durum_guncelle("🟢 Şahin Hazır.", "#2ecc71")

    def ekrani_guncelle(self, ulke, sehir, enlem, boylam, yeni_kredi):
        self.konum_etiket.configure(text=f"{ulke}, {sehir}")
        self.koordinat_etiket.configure(text=f"Koordinat: {enlem}, {boylam}")
        self.harita.set_position(enlem, boylam)
        self.harita.set_zoom(11)
        self.harita.delete_all_marker()
        self.harita.set_marker(enlem, boylam, text=sehir)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    uygulama = Geoanalyst()
    uygulama.mainloop()
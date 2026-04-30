import customtkinter as ctk

# 🛡️ Privacy-First Konfigürasyonu:
# Tema değişiklikleri sadece RAM üzerinde işletim sisteminin native API'leri ile yapılır.
# Koyu/Açık mod tercihi için hiçbir dış sunucuya veya Windows telemetrisine ping atılmaz.

class SecureDNSSwitcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Temel Pencere Ayarları ---
        self.title("Secure-DNS Switcher | Zero-Telemetry")
        self.geometry("600x450")
        self.resizable(False, False)

        # 1. Farklılaştırma: Vurgu Rengi (Accent Color)
        # Diğer projenden ayırmak için ağ/siber güvenlik tematik rengi olan yeşili seçiyoruz.
        ctk.set_default_color_theme("green") 

        # Varsayılan başlangıç modu (Dark)
        ctk.set_appearance_mode("dark")

        # --- Grid Sistemi ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Ana Çerçeve (Main Frame)
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # --- Üst Bar (Başlık ve Tema Şalteri İçin) ---
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=10)
        
        # Başlık Etiketi
        self.title_label = ctk.CTkLabel(
            self.top_bar, 
            text="Secure-DNS Switcher", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=10)

        # 2. Farklılaştırma: Açık/Koyu Mod Şalteri (Toggle Switch)
        self.appearance_switch = ctk.CTkSwitch(
            self.top_bar, 
            text="Dark Mode", 
            command=self.toggle_appearance_mode
        )
        self.appearance_switch.pack(side="right", padx=10)
        self.appearance_switch.select() # Varsayılan olarak şalteri açık (Dark) konumuna getir

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame, 
            text="Privacy-First Network Tool", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 20))

        # Gelecek aşamalar için Placeholder (Yer Tutucu) Alanlar
        self.adapter_label = ctk.CTkLabel(self.main_frame, text="[Ağ Bağdaştırıcıları Buraya Gelecek]")
        self.adapter_label.pack(pady=10)

        self.dns_list_label = ctk.CTkLabel(self.main_frame, text="[Güvenli DNS Listesi Buraya Gelecek]")
        self.dns_list_label.pack(pady=10)

        self.action_button = ctk.CTkButton(self.main_frame, text="DNS Değiştir / Test Et (İnaktif)")
        self.action_button.pack(pady=20)

    # ⚙️ Şalterin Tetiklediği (Trigger) Fonksiyon
    def toggle_appearance_mode(self):
        if self.appearance_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.appearance_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.appearance_switch.configure(text="Light Mode")

if __name__ == "__main__":
    app = SecureDNSSwitcherApp()
    app.mainloop()
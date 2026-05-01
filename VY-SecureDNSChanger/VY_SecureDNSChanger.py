import customtkinter as ctk
import wmi
import subprocess
import ctypes
import sys

# 🛡️ UAC (User Account Control) Yönetici İzni Kontrolü
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Eğer program yönetici haklarına sahip değilse, kendini yönetici olarak yeniden başlatır
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# 🛡️ Jeopolitik Filtreli DNS Veritabanı (Vendor-Neutral ve Privacy-First)
DNS_SERVERS = {
    "Quad9 (İsviçre) - Önerilen / Malware Filtreli": ["9.9.9.9", "149.112.112.112"],
    "Mullvad (İsveç) - Gizlilik Odaklı / Sansürsüz": ["194.242.2.4", "194.242.2.5"],
    "Cloudflare (ABD) - Hızlı / Riskli (Veri İşler)": ["1.1.1.1", "1.0.0.1"],
    "Google (ABD) - Kesinlikle Önerilmez (Telemetri)": ["8.8.8.8", "8.8.4.4"]
}

class SecureDNSSwitcherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Secure-DNS Switcher | Zero-Telemetry")
        self.geometry("600x450")
        self.resizable(False, False)
        ctk.set_default_color_theme("green") 
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # --- Üst Bar ---
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(self.top_bar, text="Secure-DNS Switcher", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        self.appearance_switch = ctk.CTkSwitch(self.top_bar, text="Dark Mode", command=self.toggle_appearance_mode)
        self.appearance_switch.pack(side="right", padx=10)
        self.appearance_switch.select()

        self.subtitle_label = ctk.CTkLabel(self.main_frame, text="Privacy-First Network Tool", font=ctk.CTkFont(size=12), text_color="gray")
        self.subtitle_label.pack(pady=(0, 20))

        # --- Ağ Bağdaştırıcıları ---
        self.adapter_label = ctk.CTkLabel(self.main_frame, text="1. Ağ Bağdaştırıcısını Seçin:", font=ctk.CTkFont(weight="bold"))
        self.adapter_label.pack(pady=(5, 0))

        self.adapter_combobox = ctk.CTkComboBox(self.main_frame, values=["Yükleniyor..."], width=400)
        self.adapter_combobox.pack(pady=(5, 10))

        # --- Aşama 3: Güvenli DNS Listesi ---
        self.dns_label = ctk.CTkLabel(self.main_frame, text="2. Uygulanacak DNS Sunucusunu Seçin:", font=ctk.CTkFont(weight="bold"))
        self.dns_label.pack(pady=(10, 0))

        # Sözlükteki anahtarları (İsimleri) listeye ekliyoruz
        self.dns_combobox = ctk.CTkComboBox(self.main_frame, values=list(DNS_SERVERS.keys()), width=400)
        self.dns_combobox.pack(pady=(5, 15))
        self.dns_combobox.set(list(DNS_SERVERS.keys())[0]) # Varsayılan olarak Quad9 seçili gelir

        # --- Aksiyon Butonu ---
        self.action_button = ctk.CTkButton(self.main_frame, text="DNS Uygula ve Önbelleği Temizle (Flush)", command=self.apply_dns_and_flush)
        self.action_button.pack(pady=20)

        # Başlangıçta ağ kartlarını tarar
        self.get_network_adapters()

    def toggle_appearance_mode(self):
        if self.appearance_switch.get() == 1:
            ctk.set_appearance_mode("dark")
            self.appearance_switch.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("light")
            self.appearance_switch.configure(text="Light Mode")

    def get_network_adapters(self):
        try:
            w = wmi.WMI()
            network_configs = w.Win32_NetworkAdapterConfiguration(IPEnabled=True)
            adapter_list = [config.Description for config in network_configs]
            
            if not adapter_list:
                adapter_list = ["Aktif ağ bağlantısı bulunamadı!"]
            
            self.adapter_combobox.configure(values=adapter_list)
            self.adapter_combobox.set(adapter_list[0]) 
            
        except Exception:
            self.adapter_combobox.configure(values=["Hata: WMI Okunamadı"])
            self.adapter_combobox.set("Hata: WMI Okunamadı")

    # ⚙️ Aşama 3 Motoru: DNS Değiştirme ve Flush İşlemi
    def apply_dns_and_flush(self):
        adapter = self.adapter_combobox.get()
        dns_choice = self.dns_combobox.get()
        
        if "Hata" in adapter or "Aktif ağ" in adapter:
            return

        primary_ip = DNS_SERVERS[dns_choice][0]
        secondary_ip = DNS_SERVERS[dns_choice][1]

        # Komut çalışırken siyah CMD pencerelerinin yanıp sönmesini engellemek için bayrak (flag)
        CREATE_NO_WINDOW = 0x08000000

        try:
            # 1. Birinci (Primary) DNS'i ayarla
            subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", adapter, "static", primary_ip, "primary"], 
                           check=True, creationflags=CREATE_NO_WINDOW)
            
            # 2. İkinci (Secondary) DNS'i ekle
            subprocess.run(["netsh", "interface", "ipv4", "add", "dnsservers", adapter, secondary_ip, "index=2"], 
                           check=True, creationflags=CREATE_NO_WINDOW)
            
            # 3. DNS Önbelleğini (Cache) Temizle
            subprocess.run(["ipconfig", "/flushdns"], 
                           check=True, creationflags=CREATE_NO_WINDOW)
            
            # Arayüz geri bildirimi (Yeşil başarılı mesajı)
            self.action_button.configure(text="İşlem Başarılı! (DNS Güncellendi)", fg_color="green")
            
        except subprocess.CalledProcessError:
            self.action_button.configure(text="Hata: Komut Çalıştırılamadı", fg_color="red")
        
        # 3 saniye sonra butonu eski haline döndür
        self.after(3000, lambda: self.action_button.configure(text="DNS Uygula ve Önbelleği Temizle (Flush)", fg_color=["#3B8ED0", "#1F6AA5"]))

if __name__ == "__main__":
    app = SecureDNSSwitcherApp()
    app.mainloop()
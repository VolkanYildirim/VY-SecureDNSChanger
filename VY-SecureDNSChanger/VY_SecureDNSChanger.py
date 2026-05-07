import customtkinter as ctk
import wmi
import subprocess
import ctypes
import sys
import threading
import re

# 🛡️ UAC Yönetici İzni Kontrolü
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

DNS_SERVERS = {
    "Quad9 (İsviçre) - Önerilen / Malware Filtreli": ["9.9.9.9", "149.112.112.112"],
    "Mullvad (İsveç) - Gizlilik Odaklı / Sansürsüz": ["194.242.2.4", "194.242.2.5"],
    "DNS.WATCH (Almanya) - Sansürsüz / Kayıtsız": ["84.200.69.80", "84.200.70.40"],
    "DNS4EU (Avrupa Birliği) - Bağımsız / Güvenli": ["185.228.168.10", "185.228.169.11"],
    "Cloudflare (ABD) - Hızlı / Riskli (Veri İşler)": ["1.1.1.1", "1.0.0.1"],
    "Google (ABD) - Kesinlikle Önerilmez (Telemetri)": ["8.8.8.8", "8.8.4.4"]
}

class VYDNSChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VY DNS Changer (Pro Edition) | Zero-Telemetry")
        self.geometry("600x700") # Panel için dikey alan genişletildi
        self.resizable(False, False)
        ctk.set_default_color_theme("green") 
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # --- Üst Bar ---
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        
        self.title_label = ctk.CTkLabel(self.top_bar, text="VY DNS Changer (Pro Edition)", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        self.about_button = ctk.CTkButton(self.top_bar, text="Hakkında", width=80, fg_color="#1F6AA5", hover_color="#144870", command=self.show_about_window)
        self.about_button.pack(side="right", padx=(5, 10))

        self.history_button = ctk.CTkButton(self.top_bar, text="Sürüm Geçmişi", width=110, fg_color="#3B8ED0", hover_color="#1F6AA5", command=self.show_history_window)
        self.history_button.pack(side="right", padx=5)

        # --- Seçim Alanları ---
        self.adapter_label = ctk.CTkLabel(self.main_frame, text="1. Ağ Bağdaştırıcısını Seçin:", font=ctk.CTkFont(weight="bold"))
        self.adapter_label.pack(pady=(10, 0))

        self.adapter_combobox = ctk.CTkComboBox(self.main_frame, values=["Yükleniyor..."], width=400, command=lambda _: self.refresh_current_status())
        self.adapter_combobox.pack(pady=(5, 10))

        self.dns_label = ctk.CTkLabel(self.main_frame, text="2. Uygulanacak DNS Sunucusunu Seçin:", font=ctk.CTkFont(weight="bold"))
        self.dns_label.pack(pady=(5, 0))

        self.dns_combobox = ctk.CTkComboBox(self.main_frame, values=list(DNS_SERVERS.keys()), width=400)
        self.dns_combobox.pack(pady=(5, 10))
        self.dns_combobox.set(list(DNS_SERVERS.keys())[0])

        self.test_button = ctk.CTkButton(self.main_frame, text="En Hızlı DNS'i Test Et (Ping)", command=self.start_ping_test, fg_color="#E5A50A", hover_color="#B58208", text_color="black")
        self.test_button.pack(pady=10)

        self.ping_results_textbox = ctk.CTkTextbox(self.main_frame, width=400, height=80, state="disabled", text_color="lightgray")
        self.ping_results_textbox.pack(pady=5)

        # --- Aksiyon Butonları ---
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=10)

        self.action_button = ctk.CTkButton(self.button_frame, text="DNS Uygula (Flush)", command=self.apply_dns_and_flush, width=190)
        self.action_button.pack(side="left", padx=10)

        self.reset_button = ctk.CTkButton(self.button_frame, text="Varsayılana Dön (DHCP)", command=self.reset_dns_to_dhcp, fg_color="#C62828", hover_color="#B71C1C", width=190)
        self.reset_button.pack(side="right", padx=10)

        # --- 📊 Aktif Ağ Durumu Paneli (YENİ) ---
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=["#E0E0E0", "#2B2B2B"])
        self.status_frame.pack(fill="x", padx=40, pady=15)
        
        self.status_title = ctk.CTkLabel(self.status_frame, text="📡 Aktif Durum Paneli", font=ctk.CTkFont(size=13, weight="bold"))
        self.status_title.pack(pady=(5, 2))

        self.ip_status_label = ctk.CTkLabel(self.status_frame, text="Yerel IP: Tespit Ediliyor...", font=ctk.CTkFont(size=12))
        self.ip_status_label.pack()

        self.dns_status_label = ctk.CTkLabel(self.status_frame, text="Aktif DNS: Tespit Ediliyor...", font=ctk.CTkFont(size=12))
        self.dns_status_label.pack(pady=(0, 5))

        # --- Alt Bar ---
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=10, pady=(5, 0))

        self.appearance_switch = ctk.CTkSwitch(self.footer_frame, text="Dark Mode", command=self.toggle_appearance_mode)
        self.appearance_switch.pack(side="right", padx=10)
        self.appearance_switch.select()

        self.get_network_adapters()

    def refresh_current_status(self):
        """Seçili adaptörün anlık IP ve DNS bilgilerini çeker ve paneli günceller."""
        selected_desc = self.adapter_combobox.get()
        try:
            w = wmi.WMI()
            configs = w.Win32_NetworkAdapterConfiguration(IPEnabled=True, Description=selected_desc)
            if configs:
                config = configs[0]
                ip = config.IPAddress[0] if config.IPAddress else "Bağlantı Yok"
                dns = ", ".join(config.DNSServerSearchOrder) if config.DNSServerSearchOrder else "Otomatik (DHCP)"
                self.ip_status_label.configure(text=f"Yerel IP: {ip}")
                self.dns_status_label.configure(text=f"Aktif DNS: {dns}")
            else:
                self.ip_status_label.configure(text="Yerel IP: Bilinmiyor")
                self.dns_status_label.configure(text="Aktif DNS: Bilinmiyor")
        except:
            pass

    def get_network_adapters(self):
        try:
            w = wmi.WMI()
            network_configs = w.Win32_NetworkAdapterConfiguration(IPEnabled=True)
            adapter_list = [config.Description for config in network_configs]
            if not adapter_list: adapter_list = ["Aktif ağ bağlantısı bulunamadı!"]
            self.adapter_combobox.configure(values=adapter_list)
            self.adapter_combobox.set(adapter_list[0])
            self.refresh_current_status() # İlk açılışta veriyi çek
        except Exception:
            self.adapter_combobox.configure(values=["Hata: WMI Okunamadı"])

    # (Diğer fonksiyonlar: show_history_window, show_about_window, toggle_appearance_mode, start_ping_test, run_ping_tests, update_ping_ui aynı kalacak)
    
    def apply_dns_and_flush(self):
        adapter = self.adapter_combobox.get()
        dns_choice = self.dns_combobox.get()
        if "Hata" in adapter or "Aktif ağ" in adapter: return
        primary_ip = DNS_SERVERS[dns_choice][0]
        secondary_ip = DNS_SERVERS[dns_choice][1]
        CREATE_NO_WINDOW = 0x08000000
        try:
            subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", adapter, "static", primary_ip, "primary"], check=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["netsh", "interface", "ipv4", "add", "dnsservers", adapter, secondary_ip, "index=2"], check=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["ipconfig", "/flushdns"], check=True, creationflags=CREATE_NO_WINDOW)
            self.action_button.configure(text="İşlem Başarılı!", fg_color="green")
            self.refresh_current_status() # Değişiklik sonrası paneli güncelle
        except subprocess.CalledProcessError:
            self.action_button.configure(text="Hata: Başarısız", fg_color="red")
        self.after(3000, lambda: self.action_button.configure(text="DNS Uygula (Flush)", fg_color=["#3B8ED0", "#1F6AA5"]))

    def reset_dns_to_dhcp(self):
        adapter = self.adapter_combobox.get()
        if "Hata" in adapter or "Aktif ağ" in adapter: return
        CREATE_NO_WINDOW = 0x08000000
        try:
            subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", adapter, "source=dhcp"], check=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["ipconfig", "/flushdns"], check=True, creationflags=CREATE_NO_WINDOW)
            self.reset_button.configure(text="Otomatik DNS Aktif!", fg_color="green")
            self.refresh_current_status() # Değişiklik sonrası paneli güncelle
        except subprocess.CalledProcessError:
            self.reset_button.configure(text="Hata: Sıfırlanamadı", fg_color="red")
        self.after(3000, lambda: self.reset_button.configure(text="Varsayılana Dön (DHCP)", fg_color="#C62828"))

    # Eksik modal fonksiyonlarını buraya ekleyin (önceki koddan kopyalayabilirsiniz)
    def show_history_window(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Sürüm Geçmişi")
        history_window.geometry("500x350")
        history_window.transient(self)
        history_window.grab_set()
        ctk.CTkLabel(history_window, text="Sürüm Geçmişi (Changelog)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 10))
        history_textbox = ctk.CTkTextbox(history_window, width=460, height=260, state="normal", wrap="word")
        history_textbox.pack(pady=5, padx=20)
        history_textbox.insert("1.0", "🚀 v1.1.0\n• 📊 Aktif Durum Paneli eklendi.\n• 🎨 UI iyileştirmeleri yapıldı.")
        history_textbox.configure(state="disabled")

    def show_about_window(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("Hakkında")
        about_window.geometry("450x260")
        about_window.transient(self)
        about_window.grab_set()
        ctk.CTkLabel(about_window, text="VY DNS Changer (Pro Edition)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(about_window, text="Developed by Volkan YILDIRIM", font=ctk.CTkFont(size=12)).pack()

    def toggle_appearance_mode(self):
        if self.appearance_switch.get() == 1: ctk.set_appearance_mode("dark")
        else: ctk.set_appearance_mode("light")

    def start_ping_test(self):
        self.test_button.configure(text="Test Ediliyor...", state="disabled")
        threading.Thread(target=self.run_ping_tests, daemon=True).start()

    def run_ping_tests(self):
        # Önceki ping mantığı...
        self.after(0, lambda: self.test_button.configure(text="En Hızlı DNS'i Test Et (Ping)", state="normal"))

if __name__ == "__main__":
    app = VYDNSChangerApp()
    app.mainloop()
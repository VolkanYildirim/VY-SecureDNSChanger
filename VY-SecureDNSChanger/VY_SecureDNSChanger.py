import customtkinter as ctk
import wmi
import subprocess
import ctypes
import sys
import threading
import re

# 🛡️ UAC (User Account Control) Yönetici İzni Kontrolü
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

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
        self.geometry("600x580") # Test sonuçları için pencereyi biraz uzattık
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
        
        self.title_label = ctk.CTkLabel(self.top_bar, text="Secure-DNS Switcher", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        self.appearance_switch = ctk.CTkSwitch(self.top_bar, text="Dark Mode", command=self.toggle_appearance_mode)
        self.appearance_switch.pack(side="right", padx=10)
        self.appearance_switch.select()

        # --- Ağ Bağdaştırıcıları ---
        self.adapter_label = ctk.CTkLabel(self.main_frame, text="1. Ağ Bağdaştırıcısını Seçin:", font=ctk.CTkFont(weight="bold"))
        self.adapter_label.pack(pady=(5, 0))

        self.adapter_combobox = ctk.CTkComboBox(self.main_frame, values=["Yükleniyor..."], width=400)
        self.adapter_combobox.pack(pady=(5, 10))

        # --- Güvenli DNS Listesi ---
        self.dns_label = ctk.CTkLabel(self.main_frame, text="2. Uygulanacak DNS Sunucusunu Seçin:", font=ctk.CTkFont(weight="bold"))
        self.dns_label.pack(pady=(5, 0))

        self.dns_combobox = ctk.CTkComboBox(self.main_frame, values=list(DNS_SERVERS.keys()), width=400)
        self.dns_combobox.pack(pady=(5, 10))
        self.dns_combobox.set(list(DNS_SERVERS.keys())[0])

        # --- Aşama 4: Gecikme (Ping) Testi Arayüzü ---
        self.test_button = ctk.CTkButton(self.main_frame, text="En Hızlı DNS'i Test Et (Ping)", command=self.start_ping_test, fg_color="#E5A50A", hover_color="#B58208")
        self.test_button.pack(pady=10)

        self.ping_results_textbox = ctk.CTkTextbox(self.main_frame, width=400, height=100, state="disabled", text_color="lightgray")
        self.ping_results_textbox.pack(pady=5)

        # --- Aksiyon Butonu (Aşama 3) ---
        self.action_button = ctk.CTkButton(self.main_frame, text="DNS Uygula ve Önbelleği Temizle (Flush)", command=self.apply_dns_and_flush)
        self.action_button.pack(pady=15)

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

    # ⚙️ Aşama 4 Motoru: Asenkron Ping Başlatıcı
    def start_ping_test(self):
        self.test_button.configure(text="Test Ediliyor... Lütfen Bekleyin", state="disabled")
        
        self.ping_results_textbox.configure(state="normal")
        self.ping_results_textbox.delete("1.0", "end")
        self.ping_results_textbox.insert("end", "🛡️ Gecikme testi başlatıldı (ICMP Ping)...\n\n")
        self.ping_results_textbox.configure(state="disabled")
        
        # Arayüzün donmaması için testi arka planda (Daemon Thread) çalıştır
        threading.Thread(target=self.run_ping_tests, daemon=True).start()

    # ⚙️ Aşama 4 Motoru: İşletim Sistemi Seviyesinde ICMP Sorgusu
    def run_ping_tests(self):
        results = {}
        CREATE_NO_WINDOW = 0x08000000
        
        for name, ips in DNS_SERVERS.items():
            primary_ip = ips[0]
            try:
                # Windows Ping Komutu: -n 1 (1 paket gönder), -w 1000 (1000ms zaman aşımı)
                output = subprocess.check_output(
                    ["ping", "-n", "1", "-w", "1000", primary_ip],
                    creationflags=CREATE_NO_WINDOW,
                    text=True,
                    errors='ignore' # İşletim sistemi dil kodlaması hatalarını yoksay
                )
                
                # Hem Türkçe (süre=, zaman=) hem İngilizce (time=) işletim sistemleri için Regex
                match = re.search(r'(?:time|s[uü]re|zaman)\s*[=<]\s*(\d+)\s*ms', output, re.IGNORECASE)
                if match:
                    results[name] = int(match.group(1))
                else:
                    results[name] = float('inf') # Zaman aşımı
            except Exception:
                results[name] = float('inf')
                
        # Test bittikten sonra sonuçları arayüze yazdırmak için ana thread'e sinyal gönder
        self.after(0, self.update_ping_ui, results)

    # ⚙️ Aşama 4 Motoru: Sonuçları UI'a Yazdırma
    def update_ping_ui(self, results):
        self.ping_results_textbox.configure(state="normal")
        
        if not results:
             self.ping_results_textbox.insert("end", "Hata: Test tamamlanamadı.\n")
             return
             
        # En düşük ms (milisaniye) değerini bul
        fastest_dns = min(results, key=results.get)
        
        for name, ms in results.items():
            if ms == float('inf'):
                text = f"❌ {name.split(' ')[0]}: Zaman Aşımı (Timeout)\n"
            else:
                marker = "🚀 [EN HIZLI] " if name == fastest_dns else "✅ "
                text = f"{marker}{name.split(' ')[0]}: {ms} ms\n"
            self.ping_results_textbox.insert("end", text)
            
        self.ping_results_textbox.configure(state="disabled")
        self.test_button.configure(text="Gecikme Testini Tekrarla", state="normal")
        
        # Kullanıcının işini kolaylaştırmak için ComboBox'ı otomatik olarak en hızlı DNS'e ayarla
        self.dns_combobox.set(fastest_dns)

    def apply_dns_and_flush(self):
        adapter = self.adapter_combobox.get()
        dns_choice = self.dns_combobox.get()
        
        if "Hata" in adapter or "Aktif ağ" in adapter:
            return

        primary_ip = DNS_SERVERS[dns_choice][0]
        secondary_ip = DNS_SERVERS[dns_choice][1]
        CREATE_NO_WINDOW = 0x08000000

        try:
            subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", adapter, "static", primary_ip, "primary"], check=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["netsh", "interface", "ipv4", "add", "dnsservers", adapter, secondary_ip, "index=2"], check=True, creationflags=CREATE_NO_WINDOW)
            subprocess.run(["ipconfig", "/flushdns"], check=True, creationflags=CREATE_NO_WINDOW)
            
            self.action_button.configure(text="İşlem Başarılı! (DNS Güncellendi)", fg_color="green")
        except subprocess.CalledProcessError:
            self.action_button.configure(text="Hata: Komut Çalıştırılamadı", fg_color="red")
        
        self.after(3000, lambda: self.action_button.configure(text="DNS Uygula ve Önbelleği Temizle (Flush)", fg_color=["#3B8ED0", "#1F6AA5"]))

if __name__ == "__main__":
    app = SecureDNSSwitcherApp()
    app.mainloop()
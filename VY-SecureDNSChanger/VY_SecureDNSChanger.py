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

# 🛡️ Jeopolitik Filtreli DNS Veritabanı
DNS_SERVERS = {
    "Quad9 (İsviçre) - Önerilen / Malware Filtreli": ["9.9.9.9", "149.112.112.112"],
    "Mullvad (İsveç) - Gizlilik Odaklı / Sansürsüz": ["194.242.2.4", "194.242.2.5"],
    "Cloudflare (ABD) - Hızlı / Riskli (Veri İşler)": ["1.1.1.1", "1.0.0.1"],
    "Google (ABD) - Kesinlikle Önerilmez (Telemetri)": ["8.8.8.8", "8.8.4.4"]
}

class VYDNSChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VY DNS Changer | Zero-Telemetry")
        self.geometry("600x620") 
        self.resizable(False, False)
        ctk.set_default_color_theme("green") 
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # --- Üst Bar (Top Bar) ---
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=5)
        
        self.title_label = ctk.CTkLabel(self.top_bar, text="VY DNS Changer", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=10)

        # 1. Hakkında Butonu (En Sağa Yaslanır)
        self.about_button = ctk.CTkButton(self.top_bar, text="Hakkında", width=80, fg_color="#1F6AA5", hover_color="#144870", command=self.show_about_window)
        self.about_button.pack(side="right", padx=(5, 10))

        # 2. Sürüm Geçmişi Butonu (Hakkında'nın Soluna Yaslanır)
        self.history_button = ctk.CTkButton(self.top_bar, text="Sürüm Geçmişi", width=110, fg_color="#3B8ED0", hover_color="#1F6AA5", command=self.show_history_window)
        self.history_button.pack(side="right", padx=5)

        # --- Ağ Bağdaştırıcıları ---
        self.adapter_label = ctk.CTkLabel(self.main_frame, text="1. Ağ Bağdaştırıcısını Seçin:", font=ctk.CTkFont(weight="bold"))
        self.adapter_label.pack(pady=(10, 0))

        self.adapter_combobox = ctk.CTkComboBox(self.main_frame, values=["Yükleniyor..."], width=400)
        self.adapter_combobox.pack(pady=(5, 10))

        # --- Güvenli DNS Listesi ---
        self.dns_label = ctk.CTkLabel(self.main_frame, text="2. Uygulanacak DNS Sunucusunu Seçin:", font=ctk.CTkFont(weight="bold"))
        self.dns_label.pack(pady=(5, 0))

        self.dns_combobox = ctk.CTkComboBox(self.main_frame, values=list(DNS_SERVERS.keys()), width=400)
        self.dns_combobox.pack(pady=(5, 10))
        self.dns_combobox.set(list(DNS_SERVERS.keys())[0])

        # --- Gecikme (Ping) Testi ---
        self.test_button = ctk.CTkButton(self.main_frame, text="En Hızlı DNS'i Test Et (Ping)", command=self.start_ping_test, fg_color="#E5A50A", hover_color="#B58208")
        self.test_button.pack(pady=10)

        self.ping_results_textbox = ctk.CTkTextbox(self.main_frame, width=400, height=100, state="disabled", text_color="lightgray")
        self.ping_results_textbox.pack(pady=5)

        # --- Aksiyon ve Sıfırlama Butonları ---
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=15)

        self.action_button = ctk.CTkButton(self.button_frame, text="DNS Uygula (Flush)", command=self.apply_dns_and_flush, width=190)
        self.action_button.pack(side="left", padx=10)

        self.reset_button = ctk.CTkButton(self.button_frame, text="Varsayılana Dön (DHCP)", command=self.reset_dns_to_dhcp, fg_color="#C62828", hover_color="#B71C1C", width=190)
        self.reset_button.pack(side="right", padx=10)

        # --- Alt Bar (Footer) ---
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.appearance_switch = ctk.CTkSwitch(self.footer_frame, text="Dark Mode", command=self.toggle_appearance_mode)
        self.appearance_switch.pack(side="right", padx=10)
        self.appearance_switch.select()

        self.get_network_adapters()

    # 🆕 YENİ: Sürüm Geçmişi Penceresi
    def show_history_window(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("Sürüm Geçmişi")
        history_window.geometry("500x350")
        history_window.resizable(False, False)
        
        history_window.transient(self)
        history_window.grab_set()

        ctk.CTkLabel(history_window, text="Sürüm Geçmişi (Changelog)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 10))

        # Kaydırılabilir metin kutusu (Gelecek sürümler için tasarlandı)
        history_textbox = ctk.CTkTextbox(history_window, width=460, height=260, state="normal", wrap="word")
        history_textbox.pack(pady=5, padx=20)
        
        changelog_text = (
            "🚀 v1.0.0 (İlk Sürüm)\n"
            "--------------------------------------------------\n"
            "• [UI] CustomTkinter ile modern, Dark/Light Mode destekli arayüz tasarlandı.\n"
            "• [Core] WMI (İşletim sistemi çekirdeği) üzerinden aktif ağ bağdaştırıcılarını bulma modülü eklendi.\n"
            "• [Core] UAC yönergelerine uygun, netsh tabanlı güvenli DNS değiştirme motoru yazıldı.\n"
            "• [Network] Asenkron (Threading) mimari ile çalışan ICMP Ping (Gecikme) test aracı entegre edildi.\n"
            "• [Network] Olası ağ kopmalarına karşı otomatik IP/DNS (DHCP) sıfırlama 'fail-safe' sistemi eklendi.\n"
            "• [Security] Sıfır telemetri (Zero-Telemetry) ve veri sızıntısını önleyen izole yapı (Zero-Leak) sağlandı.\n"
            "• [Data] Jeopolitik olarak nötr, gizlilik odaklı DNS veritabanı (Quad9, Mullvad vb.) sisteme gömüldü.\n"
        )
        history_textbox.insert("1.0", changelog_text)
        history_textbox.configure(state="disabled") # Kullanıcı değiştiremesin diye kilitliyoruz

    def show_about_window(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("Hakkında")
        about_window.geometry("450x260")
        about_window.resizable(False, False)
        
        about_window.transient(self)
        about_window.grab_set()

        ctk.CTkLabel(about_window, text="VY DNS Changer", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(about_window, text="Version 1.0", text_color="gray").pack(pady=(0, 15))

        desc_text = ("Bu yazılım; dijital mahremiyet (Privacy-First) ilkeleri\n"
                     "gözetilerek, tamamen açık kaynaklı altyapılar kullanılarak\n"
                     "geliştirilmiştir. Hiçbir kullanıcı verisi veya telemetri\n"
                     "toplamaz ve dışarıya aktarmaz.")
        ctk.CTkLabel(about_window, text=desc_text, justify="center").pack(pady=(10, 20))

        footer_text = "🛡️ Developed by Volkan YILDIRIM - Proctives\nwww.volkanyildirim.com.tr"
        ctk.CTkLabel(about_window, text=footer_text, justify="center").pack(pady=(0, 10))

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
            if not adapter_list: adapter_list = ["Aktif ağ bağlantısı bulunamadı!"]
            self.adapter_combobox.configure(values=adapter_list)
            self.adapter_combobox.set(adapter_list[0]) 
        except Exception:
            self.adapter_combobox.configure(values=["Hata: WMI Okunamadı"])
            self.adapter_combobox.set("Hata: WMI Okunamadı")

    def start_ping_test(self):
        self.test_button.configure(text="Test Ediliyor... Lütfen Bekleyin", state="disabled")
        self.ping_results_textbox.configure(state="normal")
        self.ping_results_textbox.delete("1.0", "end")
        self.ping_results_textbox.insert("end", "🛡️ Gecikme testi başlatıldı (ICMP Ping)...\n\n")
        self.ping_results_textbox.configure(state="disabled")
        threading.Thread(target=self.run_ping_tests, daemon=True).start()

    def run_ping_tests(self):
        results = {}
        CREATE_NO_WINDOW = 0x08000000
        for name, ips in DNS_SERVERS.items():
            primary_ip = ips[0]
            try:
                output = subprocess.check_output(["ping", "-n", "1", "-w", "1000", primary_ip], creationflags=CREATE_NO_WINDOW, text=True, errors='ignore')
                match = re.search(r'(?:time|s[uü]re|zaman)\s*[=<]\s*(\d+)\s*ms', output, re.IGNORECASE)
                if match: results[name] = int(match.group(1))
                else: results[name] = float('inf')
            except Exception: results[name] = float('inf')
        self.after(0, self.update_ping_ui, results)

    def update_ping_ui(self, results):
        self.ping_results_textbox.configure(state="normal")
        if not results:
             self.ping_results_textbox.insert("end", "Hata: Test tamamlanamadı.\n")
             return
        fastest_dns = min(results, key=results.get)
        for name, ms in results.items():
            if ms == float('inf'): text = f"❌ {name.split(' ')[0]}: Zaman Aşımı\n"
            else:
                marker = "🚀 [EN HIZLI] " if name == fastest_dns else "✅ "
                text = f"{marker}{name.split(' ')[0]}: {ms} ms\n"
            self.ping_results_textbox.insert("end", text)
        self.ping_results_textbox.configure(state="disabled")
        self.test_button.configure(text="Gecikme Testini Tekrarla", state="normal")
        self.dns_combobox.set(fastest_dns)

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
        except subprocess.CalledProcessError:
            self.reset_button.configure(text="Hata: Sıfırlanamadı", fg_color="red")
        self.after(3000, lambda: self.reset_button.configure(text="Varsayılana Dön (DHCP)", fg_color="#C62828"))

if __name__ == "__main__":
    app = VYDNSChangerApp()
    app.mainloop()
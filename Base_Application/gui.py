# gui.py
import tkinter as tk
from tkinter import scrolledtext
import config
from utils import AppState
from comms import MqttManager

class PowerDashboardGUI:
    def __init__(self, root, app_state, mqtt_manager):
        self.root = root
        self.state: AppState = app_state
        self.mqtt_manager: MqttManager = mqtt_manager
        
        self.setup_ui()
        
    def setup_ui(self):
        self.root.configure(bg=config.BG_COLOR)
        
        # Pasek Statusu MQTT na górze
        self.header = tk.Frame(self.root, bg="#111")
        self.header.pack(fill="x")
        self.lbl_mqtt_status = tk.Label(self.header, text="MQTT: --", bg="#111", fg="white", font=("Arial", 14, "bold"))
        self.lbl_mqtt_status.pack(side="left", padx=15, pady=10)
        
        self.main_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panel lewy: Odczyty
        self.left_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR)
        self.left_frame.pack(side="left", fill="both", expand=True)
        
        # Panel prawy: Sterowanie i konsola
        self.right_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR, width=450)
        self.right_frame.pack(side="right", fill="y", padx=10)
        self.right_frame.pack_propagate(False)
        
        self._build_telemetry_panel()
        self._build_control_panel()
        
    def _build_telemetry_panel(self):
        # 1. Odczyty z baterii
        bat_frame = tk.LabelFrame(self.left_frame, text="Napięcia Baterii (20V MAX)", bg=config.BG_COLOR, fg="#00ff00", font=("Arial", 12))
        bat_frame.pack(fill="x", pady=5)
        self.lbl_bats = []
        for i in range(4):
            lbl = tk.Label(bat_frame, text=f"Bateria {i+1}: 0.00 V", bg=config.BG_COLOR, fg="white", font=("Consolas", 18))
            lbl.pack(anchor="w", padx=15, pady=2)
            self.lbl_bats.append(lbl)
            
        # 2. Odczyt Temperatury
        temp_frame = tk.LabelFrame(self.left_frame, text="Czujnik DS18B20", bg=config.BG_COLOR, fg="#00ccff", font=("Arial", 12))
        temp_frame.pack(fill="x", pady=10)
        self.lbl_temp = tk.Label(temp_frame, text="Temp: 0.0 °C", bg=config.BG_COLOR, fg="#00ccff", font=("Consolas", 20, "bold"))
        self.lbl_temp.pack(anchor="w", padx=15, pady=5)
        
        # 3. Odczyty ADC z 6 Linii (ACS712)
        adc_frame = tk.LabelFrame(self.left_frame, text="Pobór Prądu Linii (ACS712)", bg=config.BG_COLOR, fg="#ffaa00", font=("Arial", 12))
        adc_frame.pack(fill="x", pady=5)
        self.lbl_adcs = {}
        # Zgrupowane nazwy żeby wyświetlić czytelnie
        keys = ["adc_wl", "adc_wr", "adc_ram", "adc_elek", "adc_sci", "adc_inne"]
        
        for key in keys:
            lbl = tk.Label(adc_frame, text=f"{key.upper()}: RAW 0 | 0.00 A", bg=config.BG_COLOR, fg="white", font=("Consolas", 14))
            lbl.pack(anchor="w", padx=15, pady=4)
            self.lbl_adcs[key] = lbl

    def _build_control_panel(self):
        # 1. 6 Przycisków zasilania + Wentylator
        ctrl_frame = tk.LabelFrame(self.right_frame, text="Zarządzanie Liniami Zasilania", bg=config.BG_COLOR, fg="#00ff00", font=("Arial", 12))
        ctrl_frame.pack(fill="x", pady=5)
        
        self.btn_switches = {}
        switches = ["S_INNE", "S_SCI", "S_ELEK", "S_RAM", "S_W_R", "S_W_L", "FAN1_ON"]
        
        for sw in switches:
            btn = tk.Button(ctrl_frame, text=f"{sw} [WYŁĄCZONY]", font=("Arial", 12, "bold"), 
                            bg=config.BTN_OFF_COLOR, fg="white", height=2,
                            command=lambda s=sw: self.mqtt_manager.toggle_switch(s))
            btn.pack(fill="x", padx=10, pady=3)
            self.btn_switches[sw] = btn
            
        # 2. Konsola na dole
        log_frame = tk.LabelFrame(self.right_frame, text="Konsola Poleceń", bg=config.BG_COLOR, fg="#ffffff")
        log_frame.pack(fill="both", expand=True, pady=10)
        self.console = scrolledtext.ScrolledText(log_frame, bg="#222", fg="#0f0", font=("Consolas", 10))
        self.console.pack(fill="both", expand=True, padx=5, pady=5)
        
    def _calc_current_acs712(self, raw_adc, key):
        """ Przelicza wartość RAW na ampery w oparciu o indywidualny punkt zera """
        # Pobierz punkt zera dla danego pinu z konfiguracji (domyślnie 3000 jak nie znajdzie)
        zero_raw = config.ACS712_ZERO_RAW.get(key, 3000)
        
        # Oblicz o ile RAW różni się od zera (może być ujemne jeśli prąd płynie w drugą stronę)
        delta_raw = raw_adc - zero_raw
        
        # Przeliczenie odchyłki RAW na różnicę napięcia na pinie ESP32 (3.3V / 4095)
        delta_v = delta_raw * (3.3 / 4095.0)
        
        # Prąd = różnica napięcia / czułość
        current_a = delta_v / config.ACS712_SENSITIVITY
        return current_a

    def update_interface(self):
        # 1. Update statusu
        self.lbl_mqtt_status.config(text=self.state.mqtt_status_text)
        if self.state.mqtt_connected:
            self.lbl_mqtt_status.config(fg="#00ff00")
        else:
            self.lbl_mqtt_status.config(fg="red")
            
        # 2. Update Baterii
        for i in range(4):
            self.lbl_bats[i].config(text=f"Bateria {i+1}: {self.state.bat_v[i]:.2f} V")
            
        # 3. Update Temperatury
        self.lbl_temp.config(text=f"Temp: {self.state.temp_c:.1f} °C")
        
        # 4. Update ADC -> Wyliczenie Amperów
        for key, lbl in self.lbl_adcs.items():
            raw = self.state.adc[key]
            current_amps = self._calc_current_acs712(raw, key) # <- DODANO PRZEKAZANIE KLUCZA
            lbl.config(text=f"{key.upper():<8}: RAW {raw:>4d}  |  {current_amps:>5.2f} A")
            
        # 5. Odświeżenie wyglądu przycisków w GUI
        for sw, btn in self.btn_switches.items():
            state = self.state.switches[sw]
            if state == 1:
                btn.config(bg=config.BTN_ON_COLOR, text=f"{sw} [WŁĄCZONY]")
            else:
                btn.config(bg=config.BTN_OFF_COLOR, text=f"{sw} [WYŁĄCZONY]")
                
        # 6. Czyszczenie buffora konsoli logów
        while self.state.logs:
            msg = self.state.logs.pop(0)
            self.console.insert(tk.END, msg + "\n")
            self.console.see(tk.END)
# utils.py

class AppState:
    """Klasa przechowująca współdzielony stan aplikacji Power"""
    def __init__(self):
        # Statusy MQTT
        self.mqtt_connected = False
        self.mqtt_status_text = "MQTT: Rozłączono"
        
        # Logi
        self.logs = [] 

        # Stany przełączników i wentylatora (0 - wyłączony, 1 - włączony)
        self.switches = {
            "S_INNE": 0,
            "S_SCI": 0,
            "S_ELEK": 0,
            "S_RAM": 0,
            "S_W_R": 0,
            "S_W_L": 0,
            "FAN1_ON": 0
        }

        # Dane telemetryczne (Odczyty)
        self.temp_c = 0.0
        self.bat_v = [0.0, 0.0, 0.0, 0.0]  # Napięcia 4 baterii
        self.adc = {
            "adc_wl": 0, 
            "adc_wr": 0, 
            "adc_ram": 0, 
            "adc_elek": 0, 
            "adc_sci": 0, 
            "adc_inne": 0
        }

    def log(self, message):
        self.logs.append(message)
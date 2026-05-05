# main.py
import tkinter as tk
from utils import AppState
from comms import MqttManager
from gui import PowerDashboardGUI

def main():
    root = tk.Tk()
    root.title("Orion Power Station Dashboard")
    root.geometry("1100x800")

    # Inicjalizacja Stanu i Modułów
    app_state = AppState()
    mqtt_manager = MqttManager(app_state)
    gui = PowerDashboardGUI(root, app_state, mqtt_manager)

    # Start MQTT
    mqtt_manager.connect()

    def main_loop():
        # Odświeżenie GUI nowymi danymi otrzymanymi z subskrypcji MQTT
        gui.update_interface()
        
        # Zapętlenie wywołania interfejsu (co 100ms)
        root.after(100, main_loop)

    main_loop()
    root.mainloop()

if __name__ == "__main__":
    main()
import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal
import time

class SerialHandler(QThread):
    data_received = Signal(float)
    connection_status = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.port_name = ""
        self.baudrate = 9600
        self.is_running = False
        self.is_connected = False
        
    def connect_serial(self, port_name):
        try:
            self.serial_port = serial.Serial(port_name, self.baudrate, timeout=1)
            self.port_name = port_name
            self.is_connected = True
            self.connection_status.emit(True, f"Conectado a {port_name}")
            return True
        except Exception as e:
            self.connection_status.emit(False, f"Error: {str(e)}")
            return False
    
    def disconnect_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
        self.connection_status.emit(False, "Desconectado")
    
    def start_reading(self):
        if self.is_connected:
            self.is_running = True
            self.start()
    
    def stop_reading(self):
        self.is_running = False
        self.wait()
    
    def run(self):
        while self.is_running and self.is_connected:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        value = float(line)
                        self.data_received.emit(value)
            except Exception as e:
                self.connection_status.emit(False, f"Error de lectura: {str(e)}")
                break
            time.sleep(0.001)  # Pequeña pausa para no saturar
    
    @staticmethod
    def get_available_ports():
        return [port.device for port in serial.tools.list_ports.comports()]
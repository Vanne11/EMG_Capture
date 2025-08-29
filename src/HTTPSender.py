import requests
import json
import time
from PySide6.QtCore import QObject, Signal, QTimer
from datetime import datetime

class HTTPSender(QObject):
    transmission_status = Signal(bool, str)
    clear_status = Signal(str)
    
    def __init__(self, receiver_url="https://tmeduca.org/emg/reciver.php", clear_url="https://tmeduca.org/emg/clear.php"):
        super().__init__()
        self.receiver_url = receiver_url
        self.clear_url = clear_url
        self.is_transmitting = False
        self.data_buffer = []
        self.session_start_time = None
        
        # Timer para envío de lotes cada 0.2 segundos
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self.send_batch)
        
    def start_transmission(self):
        """Inicia la transmisión de datos"""
        if not self.is_transmitting:
            self.is_transmitting = True
            self.session_start_time = time.time() * 1000  # Tiempo en ms
            self.data_buffer.clear()
            self.batch_timer.start(200)  # 200ms = 0.2 segundos
            self.transmission_status.emit(True, "Transmisión web iniciada")
            return True
        return False
    
    def stop_transmission(self):
        """Detiene la transmisión de datos"""
        if self.is_transmitting:
            self.batch_timer.stop()
            # Enviar último lote si hay datos pendientes
            if self.data_buffer:
                self.send_batch()
            self.is_transmitting = False
            self.transmission_status.emit(False, "Transmisión web detenida")
            return True
        return False
    
    def add_sample(self, raw_value, filtered_value):
        """Agrega una muestra al buffer para envío en lote"""
        if not self.is_transmitting or self.session_start_time is None:
            return
            
        current_time = time.time() * 1000
        relative_time = current_time - self.session_start_time
        
        sample = {
            "time_ms": round(relative_time, 1),
            "raw": raw_value,
            "filtered": round(filtered_value, 1)
        }
        
        self.data_buffer.append(sample)
    
    def send_batch(self):
        """Envía el lote actual de datos al servidor"""
        if not self.data_buffer:
            return
            
        try:
            # Preparar datos del lote
            batch_data = {
                "timestamp": datetime.now().isoformat(),
                "batch_time_ms": time.time() * 1000,
                "samples": self.data_buffer.copy()
            }
            
            # Enviar POST request
            response = requests.post(
                self.receiver_url,
                json=batch_data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Éxito - limpiar buffer
                self.data_buffer.clear()
            else:
                self.transmission_status.emit(False, f"Error HTTP: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.transmission_status.emit(False, f"Error de conexión: {str(e)}")
        except Exception as e:
            self.transmission_status.emit(False, f"Error: {str(e)}")
    
    def clear_server_data(self):
        """Envía petición para limpiar datos del servidor"""
        try:
            response = requests.post(
                self.clear_url,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.clear_status.emit("Datos del servidor borrados exitosamente")
            else:
                self.clear_status.emit(f"Error al borrar datos: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.clear_status.emit(f"Error de conexión al borrar: {str(e)}")
        except Exception as e:
            self.clear_status.emit(f"Error al borrar: {str(e)}")
import requests
import json
import time
import threading
from queue import Queue
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
        
        # Queue para peticiones HTTP
        self.http_queue = Queue()
        
        # Hilo de trabajo para HTTP
        self.http_thread = None
        self.http_thread_running = False
        
        # Timer para envío de lotes cada 0.2 segundos (en hilo principal, pero no-bloqueante)
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._queue_batch_send)
        
        # Iniciar hilo HTTP
        self._start_http_thread()
    
    def _start_http_thread(self):
        """Inicia el hilo dedicado para peticiones HTTP"""
        if not self.http_thread_running:
            self.http_thread_running = True
            self.http_thread = threading.Thread(target=self._http_worker, daemon=True)
            self.http_thread.start()
    
    def _http_worker(self):
        """Worker thread que procesa peticiones HTTP de forma continua"""
        while self.http_thread_running:
            try:
                # Obtener próxima petición con timeout
                request = self.http_queue.get(timeout=1.0)
                
                if request['type'] == 'batch':
                    self._send_batch_http(request['data'])
                elif request['type'] == 'clear':
                    self._clear_server_http()
                    
                self.http_queue.task_done()
                
            except:
                # Timeout o queue vacía, continuar
                continue
    
    def start_transmission(self):
        """Inicia la transmisión de datos - NO BLOQUEANTE"""
        if not self.is_transmitting:
            self.is_transmitting = True
            self.session_start_time = time.time() * 1000  # Tiempo en ms
            self.data_buffer.clear()
            self.batch_timer.start(200)  # 200ms = 0.2 segundos
            self.transmission_status.emit(True, "Transmisión web iniciada")
            return True
        return False
    
    def stop_transmission(self):
        """Detiene la transmisión de datos - NO BLOQUEANTE"""
        if self.is_transmitting:
            self.batch_timer.stop()
            
            # Enviar último lote si hay datos pendientes
            if self.data_buffer:
                self._queue_batch_send()
                
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
    
    def _queue_batch_send(self):
        """Encola el envío del lote actual - NO BLOQUEANTE"""
        if not self.data_buffer:
            return
        
        # Preparar datos del lote
        batch_data = {
            "timestamp": datetime.now().isoformat(),
            "batch_time_ms": time.time() * 1000,
            "samples": self.data_buffer.copy()
        }
        
        # Limpiar buffer después de copiar
        self.data_buffer.clear()
        
        # Encolar para envío en hilo HTTP
        self.http_queue.put({
            'type': 'batch',
            'data': batch_data
        })
    
    def _send_batch_http(self, batch_data):
        """Envía el lote al servidor - EJECUTA EN HILO HTTP"""
        try:
            response = requests.post(
                self.receiver_url,
                json=batch_data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                self.transmission_status.emit(False, f"Error HTTP: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.transmission_status.emit(False, f"Error de conexión: {str(e)}")
        except Exception as e:
            self.transmission_status.emit(False, f"Error: {str(e)}")
    
    def clear_server_data(self):
        """Encola petición para limpiar datos del servidor - NO BLOQUEANTE"""
        self.http_queue.put({'type': 'clear'})
    
    def _clear_server_http(self):
        """Ejecuta la limpieza del servidor - EJECUTA EN HILO HTTP"""
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
    
    def __del__(self):
        """Cleanup al destruir el objeto"""
        self.http_thread_running = False
        if self.http_thread:
            self.http_thread.join(timeout=1.0)
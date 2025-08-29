import csv
import os
import time
from datetime import datetime
from PySide6.QtCore import QObject, Signal

class DataLogger(QObject):
    log_status = Signal(str)
    
    def __init__(self, base_directory="data"):
        super().__init__()
        self.base_directory = base_directory
        self.current_file = None
        self.csv_writer = None
        self.file_handle = None
        self.is_logging = False
        self.sample_count = 0
        self.session_start_time = None  # Tiempo de inicio de la sesión en ms
        
        # Crear directorio si no existe
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)
    
    def start_logging(self, session_name=None):
        if self.is_logging:
            return False
            
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if session_name:
                filename = f"{session_name}_{timestamp}.csv"
            else:
                filename = f"emg_session_{timestamp}.csv"
            
            self.current_file = os.path.join(self.base_directory, filename)
            
            # Abrir archivo y crear writer
            self.file_handle = open(self.current_file, 'w', newline='')
            self.csv_writer = csv.writer(self.file_handle)
            
            # Escribir encabezados actualizados
            self.csv_writer.writerow([
                'timestamp_iso',           # Timestamp absoluto ISO
                'time_ms',                # Tiempo relativo en milisegundos desde inicio
                'sample_number', 
                'raw_value_mv',           # Valor crudo en mV
                'filtered_value_uv'       # Valor filtrado en µV
            ])
            
            self.is_logging = True
            self.sample_count = 0
            self.session_start_time = time.time() * 1000  # Tiempo de inicio en ms
            self.log_status.emit(f"Iniciando grabación: {filename}")
            return True
            
        except Exception as e:
            self.log_status.emit(f"Error al iniciar grabación: {str(e)}")
            return False
    
    def log_sample(self, raw_value_mv, filtered_value_uv):
        if not self.is_logging or not self.csv_writer:
            return
            
        try:
            current_time = time.time() * 1000
            timestamp_iso = datetime.now().isoformat()
            time_ms = current_time - self.session_start_time
            self.sample_count += 1
            
            self.csv_writer.writerow([
                timestamp_iso,
                f"{time_ms:.1f}",  # Tiempo relativo con 1 decimal
                self.sample_count,
                f"{raw_value_mv:.3f}",      # mV con 3 decimales
                f"{filtered_value_uv:.1f}"  # µV con 1 decimal
            ])
            
            # Flush cada 100 muestras para asegurar escritura
            if self.sample_count % 100 == 0:
                self.file_handle.flush()
                
        except Exception as e:
            self.log_status.emit(f"Error al escribir muestra: {str(e)}")
    
    def stop_logging(self):
        if not self.is_logging:
            return
            
        try:
            if self.file_handle:
                self.file_handle.close()
                
            self.is_logging = False
            self.log_status.emit(f"Grabación finalizada. {self.sample_count} muestras guardadas en {self.current_file}")
            
            self.current_file = None
            self.csv_writer = None
            self.file_handle = None
            self.session_start_time = None
            
        except Exception as e:
            self.log_status.emit(f"Error al finalizar grabación: {str(e)}")
    
    def get_current_file(self):
        return self.current_file
    
    def get_sample_count(self):
        return self.sample_count
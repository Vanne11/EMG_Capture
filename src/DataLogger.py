import csv
import os
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
            
            # Escribir encabezados
            self.csv_writer.writerow([
                'timestamp',
                'sample_number', 
                'raw_value',
                'filtered_value'
            ])
            
            self.is_logging = True
            self.sample_count = 0
            self.log_status.emit(f"Iniciando grabación: {filename}")
            return True
            
        except Exception as e:
            self.log_status.emit(f"Error al iniciar grabación: {str(e)}")
            return False
    
    def log_sample(self, raw_value, filtered_value):
        if not self.is_logging or not self.csv_writer:
            return
            
        try:
            timestamp = datetime.now().isoformat()
            self.sample_count += 1
            
            self.csv_writer.writerow([
                timestamp,
                self.sample_count,
                raw_value,
                filtered_value
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
            
        except Exception as e:
            self.log_status.emit(f"Error al finalizar grabación: {str(e)}")
    
    def get_current_file(self):
        return self.current_file
    
    def get_sample_count(self):
        return self.sample_count
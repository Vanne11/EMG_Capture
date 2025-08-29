import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from SerialHandler import SerialHandler
from SignalProcessor import SignalProcessor
from DataLogger import DataLogger
from WebSocketServer import WebSocketServer
from HTTPSender import HTTPSender
from MainWindow import MainWindow

class EMGApplication(QObject):
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.serial_handler = SerialHandler()
        self.signal_processor = SignalProcessor()
        self.data_logger = DataLogger()
        self.websocket_server = WebSocketServer()
        self.http_sender = HTTPSender()
        self.main_window = MainWindow()
        
        # Variables de estado
        self.is_acquiring = False
        self.is_recording = False
        self.is_websocket_running = False
        self.is_web_transmitting = False
        
        # Timer para actualizar progreso de calibración
        self.calibration_timer = QTimer()
        self.calibration_timer.timeout.connect(self.update_calibration_progress)
        
        # Conectar señales
        self.setup_connections()
        
        # Configurar interfaz inicial
        self.setup_initial_state()
    
    def setup_connections(self):
        # Conexiones del SerialHandler
        self.serial_handler.data_received.connect(self.process_data)
        self.serial_handler.connection_status.connect(self.update_connection_status)
        
        # Conexiones del DataLogger
        self.data_logger.log_status.connect(self.main_window.log_message)
        
        # Conexiones del WebSocketServer
        self.websocket_server.server_status.connect(self.update_websocket_status)
        self.websocket_server.client_connected.connect(self.update_client_count)
        
        # Conexiones del HTTPSender
        self.http_sender.transmission_status.connect(self.update_web_transmission_status)
        self.http_sender.clear_status.connect(self.main_window.log_message)
        
        # Conexiones de la interfaz
        self.main_window.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.main_window.connect_btn.clicked.connect(self.toggle_connection)
        self.main_window.start_btn.clicked.connect(self.start_acquisition)
        self.main_window.stop_btn.clicked.connect(self.stop_acquisition)
        self.main_window.record_btn.clicked.connect(self.toggle_recording)
        self.main_window.websocket_btn.clicked.connect(self.toggle_websocket)
        
        # Conexiones de transmisión web
        self.main_window.web_transmission_btn.clicked.connect(self.toggle_web_transmission)
        self.main_window.clear_server_btn.clicked.connect(self.clear_server_data)
        
        # Conexión del botón de calibración
        self.main_window.calibrate_btn.clicked.connect(self.start_calibration)
        
        # Conexiones de filtros
        self.main_window.lowpass_check.toggled.connect(lambda: self.update_filter('lowpass'))
        self.main_window.highpass_check.toggled.connect(lambda: self.update_filter('highpass'))
        self.main_window.notch_check.toggled.connect(lambda: self.update_filter('notch'))
        self.main_window.moving_avg_check.toggled.connect(lambda: self.update_filter('moving_avg'))
        
        # Conexiones de parámetros de filtros
        self.main_window.lowpass_freq.valueChanged.connect(self.update_filter_params)
        self.main_window.highpass_freq.valueChanged.connect(self.update_filter_params)
        self.main_window.notch_freq.valueChanged.connect(self.update_filter_params)
        self.main_window.moving_avg_window.valueChanged.connect(self.update_filter_params)
    
    def setup_initial_state(self):
        self.refresh_ports()
        self.main_window.show()
    
    def refresh_ports(self):
        ports = SerialHandler.get_available_ports()
        self.main_window.port_combo.clear()
        self.main_window.port_combo.addItems(ports)
    
    def toggle_connection(self):
        if not self.serial_handler.is_connected:
            port = self.main_window.port_combo.currentText()
            if port and self.serial_handler.connect_serial(port):
                self.main_window.connect_btn.setText("Desconectar")
                self.main_window.start_btn.setEnabled(True)
        else:
            self.stop_acquisition()
            self.serial_handler.disconnect_serial()
            self.main_window.connect_btn.setText("Conectar")
            self.main_window.start_btn.setEnabled(False)
            self.main_window.stop_btn.setEnabled(False)
    
    def start_acquisition(self):
        if self.serial_handler.is_connected:
            # Reiniciar referencia de tiempo cuando empiece la adquisición
            self.main_window.reset_time_reference()
            
            self.serial_handler.start_reading()
            self.is_acquiring = True
            self.main_window.start_btn.setEnabled(False)
            self.main_window.stop_btn.setEnabled(True)
            self.main_window.log_message("Adquisición iniciada")
    
    def stop_acquisition(self):
        if self.is_acquiring:
            self.serial_handler.stop_reading()
            self.is_acquiring = False
            self.main_window.start_btn.setEnabled(True)
            self.main_window.stop_btn.setEnabled(False)
            self.main_window.log_message("Adquisición detenida")
            
            # Detener grabación si está activa
            if self.is_recording:
                self.toggle_recording()
            
            # Detener transmisión web si está activa
            if self.is_web_transmitting:
                self.toggle_web_transmission()
            
            # Detener calibración si está activa
            if self.signal_processor.is_calibrating:
                self.stop_calibration()
    
    def start_calibration(self):
        """Inicia el proceso de calibración EMG"""
        if not self.is_acquiring:
            self.main_window.log_message("Error: Debe iniciar la adquisición antes de calibrar")
            return
            
        duration = self.main_window.calibration_duration.value()
        
        if self.signal_processor.start_calibration(duration):
            self.main_window.set_calibration_state(True)
            self.calibration_timer.start(100)  # Actualizar cada 100ms
            self.main_window.log_message(f"Iniciando calibración de {duration} segundos - manténgase en reposo")
    
    def stop_calibration(self):
        """Detiene la calibración en curso"""
        if self.signal_processor.is_calibrating:
            success, offset_mv = self.signal_processor.finish_calibration()
            self.main_window.set_calibration_state(False)
            self.main_window.set_calibration_result(success, offset_mv)
            self.calibration_timer.stop()
            
            if success:
                self.main_window.log_message(f"Calibración completada. Offset: {offset_mv:.1f}mV")
            else:
                self.main_window.log_message("Error en la calibración")
    
    def update_calibration_progress(self):
        """Actualiza el progreso de calibración"""
        if self.signal_processor.is_calibrating:
            progress = self.signal_processor.get_calibration_progress()
            self.main_window.update_calibration_progress(progress)
            
            if progress >= 1.0:
                self.stop_calibration()
    
    def toggle_recording(self):
        if not self.is_recording:
            if self.data_logger.start_logging():
                self.is_recording = True
                self.main_window.record_btn.setText("Detener Grabación")
                self.main_window.record_status.setText("Grabando...")
        else:
            self.data_logger.stop_logging()
            self.is_recording = False
            self.main_window.record_btn.setText("Iniciar Grabación")
            self.main_window.record_status.setText("Sin grabación")
    
    def toggle_websocket(self):
        if not self.is_websocket_running:
            self.websocket_server.start_server()
            self.main_window.websocket_btn.setText("Detener Servidor")
        else:
            self.websocket_server.stop_server()
            self.main_window.websocket_btn.setText("Iniciar Servidor")
    
    def toggle_web_transmission(self):
        if not self.is_web_transmitting:
            if not self.is_acquiring:
                self.main_window.log_message("Error: Debe iniciar la adquisición antes de transmitir")
                return
            if self.http_sender.start_transmission():
                self.main_window.web_transmission_btn.setText("Detener Transmisión Web")
        else:
            if self.http_sender.stop_transmission():
                self.main_window.web_transmission_btn.setText("Iniciar Transmisión Web")
    
    def clear_server_data(self):
        self.http_sender.clear_server_data()
    
    def update_web_transmission_status(self, transmitting, message):
        self.is_web_transmitting = transmitting
        self.main_window.web_transmission_status.setText(message)
        self.main_window.log_message(message)
    
    def process_data(self, raw_value):
        # Procesar con conversión EMG y filtros
        muscle_potential_uv = self.signal_processor.add_sample(raw_value)
        
        # Actualizar gráficos
        self.main_window.add_data_point(raw_value, muscle_potential_uv)
        
        # Guardar datos si se está grabando con valores reales
        if self.is_recording:
            # Convertir raw_value a mV para el log
            voltage_mv = raw_value * self.signal_processor.ads_resolution
            self.data_logger.log_sample(voltage_mv, muscle_potential_uv)
        
        # Enviar por WebSocket si está activo
        if self.is_websocket_running:
            self.websocket_server.send_data(raw_value, muscle_potential_uv)
        
        # Enviar por HTTP si está activo
        if self.is_web_transmitting:
            voltage_mv = raw_value * self.signal_processor.ads_resolution
            self.http_sender.add_sample(voltage_mv, muscle_potential_uv)
    
    def update_connection_status(self, connected, message):
        self.main_window.connection_status.setText(message)
        self.main_window.log_message(message)
    
    def update_websocket_status(self, running, message):
        self.is_websocket_running = running
        self.main_window.websocket_status.setText(message)
        self.main_window.log_message(message)
    
    def update_client_count(self, count):
        self.main_window.clients_count.setText(f"Clientes: {count}")
    
    def update_filter(self, filter_type):
        checkbox_map = {
            'lowpass': self.main_window.lowpass_check,
            'highpass': self.main_window.highpass_check,
            'notch': self.main_window.notch_check,
            'moving_avg': self.main_window.moving_avg_check
        }
        
        if filter_type in checkbox_map:
            active = checkbox_map[filter_type].isChecked()
            self.signal_processor.set_filter_state(filter_type, active)
    
    def update_filter_params(self):
        params = {
            'lowpass_cutoff': self.main_window.lowpass_freq.value(),
            'highpass_cutoff': self.main_window.highpass_freq.value(),
            'notch_freq': self.main_window.notch_freq.value(),
            'moving_avg_window': self.main_window.moving_avg_window.value()
        }
        self.signal_processor.set_filter_params(**params)
    
    def run(self):
        return self.main_window.show()

def main():
    app = QApplication(sys.argv)
    emg_app = EMGApplication()
    emg_app.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
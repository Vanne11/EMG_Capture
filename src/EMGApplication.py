import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, pyqtSignal
from SerialHandler import SerialHandler
from SignalProcessor import SignalProcessor
from DataLogger import DataLogger
from WebSocketServer import WebSocketServer
from MainWindow import MainWindow

class EMGApplication(QObject):
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.serial_handler = SerialHandler()
        self.signal_processor = SignalProcessor()
        self.data_logger = DataLogger()
        self.websocket_server = WebSocketServer()
        self.main_window = MainWindow()
        
        # Variables de estado
        self.is_acquiring = False
        self.is_recording = False
        self.is_websocket_running = False
        
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
        
        # Conexiones de la interfaz
        self.main_window.refresh_ports_btn.clicked.connect(self.refresh_ports)
        self.main_window.connect_btn.clicked.connect(self.toggle_connection)
        self.main_window.start_btn.clicked.connect(self.start_acquisition)
        self.main_window.stop_btn.clicked.connect(self.stop_acquisition)
        self.main_window.record_btn.clicked.connect(self.toggle_recording)
        self.main_window.websocket_btn.clicked.connect(self.toggle_websocket)
        
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
    
    def process_data(self, raw_value):
        # Procesar con filtros
        filtered_value = self.signal_processor.add_sample(raw_value)
        
        # Actualizar gráficos
        self.main_window.add_data_point(raw_value, filtered_value)
        
        # Guardar datos si se está grabando
        if self.is_recording:
            self.data_logger.log_sample(raw_value, filtered_value)
        
        # Enviar por WebSocket si está activo
        if self.is_websocket_running:
            self.websocket_server.send_data(raw_value, filtered_value)
    
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
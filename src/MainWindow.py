from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QLabel, QGroupBox, 
                               QCheckBox, QDoubleSpinBox, QSpinBox, QTextEdit,
                               QSplitter, QFrame)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMG Real-Time Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Variables para gráficos
        self.plot_data_raw = []
        self.plot_data_filtered = []
        self.max_points = 1000
        
        # Timer para actualización de gráficos
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(50)  # Actualizar cada 50ms
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel de control (izquierda)
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # Panel de gráficos (derecha)
        plot_panel = self.create_plot_panel()
        splitter.addWidget(plot_panel)
        
        # Configurar proporción del splitter
        splitter.setSizes([300, 900])
    
    def create_control_panel(self):
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumWidth(350)
        layout = QVBoxLayout(panel)
        
        # Conexión Serial
        serial_group = QGroupBox("Conexión Serial")
        serial_layout = QVBoxLayout(serial_group)
        
        self.port_combo = QComboBox()
        self.refresh_ports_btn = QPushButton("Actualizar Puertos")
        self.connect_btn = QPushButton("Conectar")
        self.connection_status = QLabel("Desconectado")
        
        serial_layout.addWidget(QLabel("Puerto:"))
        serial_layout.addWidget(self.port_combo)
        serial_layout.addWidget(self.refresh_ports_btn)
        serial_layout.addWidget(self.connect_btn)
        serial_layout.addWidget(self.connection_status)
        
        # Control de Adquisición
        acquisition_group = QGroupBox("Adquisición")
        acquisition_layout = QVBoxLayout(acquisition_group)
        
        self.start_btn = QPushButton("Iniciar")
        self.stop_btn = QPushButton("Detener")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        acquisition_layout.addWidget(self.start_btn)
        acquisition_layout.addWidget(self.stop_btn)
        
        # Filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QVBoxLayout(filters_group)
        
        # Filtro Pasa-bajas
        self.lowpass_check = QCheckBox("Pasa-bajas")
        self.lowpass_freq = QDoubleSpinBox()
        self.lowpass_freq.setRange(1.0, 100.0)
        self.lowpass_freq.setValue(30.0)
        self.lowpass_freq.setSuffix(" Hz")
        
        # Filtro Pasa-altas
        self.highpass_check = QCheckBox("Pasa-altas")
        self.highpass_freq = QDoubleSpinBox()
        self.highpass_freq.setRange(0.1, 10.0)
        self.highpass_freq.setValue(0.5)
        self.highpass_freq.setSuffix(" Hz")
        
        # Filtro Notch
        self.notch_check = QCheckBox("Notch")
        self.notch_freq = QDoubleSpinBox()
        self.notch_freq.setRange(45.0, 65.0)
        self.notch_freq.setValue(50.0)
        self.notch_freq.setSuffix(" Hz")
        
        # Promedio móvil
        self.moving_avg_check = QCheckBox("Promedio móvil")
        self.moving_avg_window = QSpinBox()
        self.moving_avg_window.setRange(2, 50)
        self.moving_avg_window.setValue(10)
        self.moving_avg_window.setSuffix(" muestras")
        
        filters_layout.addWidget(self.lowpass_check)
        filters_layout.addWidget(self.lowpass_freq)
        filters_layout.addWidget(self.highpass_check)
        filters_layout.addWidget(self.highpass_freq)
        filters_layout.addWidget(self.notch_check)
        filters_layout.addWidget(self.notch_freq)
        filters_layout.addWidget(self.moving_avg_check)
        filters_layout.addWidget(self.moving_avg_window)
        
        # Grabación
        recording_group = QGroupBox("Grabación")
        recording_layout = QVBoxLayout(recording_group)
        
        self.record_btn = QPushButton("Iniciar Grabación")
        self.record_status = QLabel("Sin grabación")
        
        recording_layout.addWidget(self.record_btn)
        recording_layout.addWidget(self.record_status)
        
        # WebSocket
        websocket_group = QGroupBox("WebSocket")
        websocket_layout = QVBoxLayout(websocket_group)
        
        self.websocket_btn = QPushButton("Iniciar Servidor")
        self.websocket_status = QLabel("Servidor detenido")
        self.clients_count = QLabel("Clientes: 0")
        
        websocket_layout.addWidget(self.websocket_btn)
        websocket_layout.addWidget(self.websocket_status)
        websocket_layout.addWidget(self.clients_count)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        # Agregar grupos al panel
        layout.addWidget(serial_group)
        layout.addWidget(acquisition_group)
        layout.addWidget(filters_group)
        layout.addWidget(recording_group)
        layout.addWidget(websocket_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        return panel
    
    def create_plot_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Configurar pyqtgraph
        pg.setConfigOptions(antialias=True)
        
        # Gráfico de señal cruda
        self.raw_plot = pg.PlotWidget(title="Señal Cruda")
        self.raw_plot.setLabel('left', 'Amplitud', 'ADC')
        self.raw_plot.setLabel('bottom', 'Tiempo', 'muestras')
        self.raw_curve = self.raw_plot.plot(pen='b', name='Raw')
        
        # Gráfico de señal filtrada
        self.filtered_plot = pg.PlotWidget(title="Señal Filtrada")
        self.filtered_plot.setLabel('left', 'Amplitud', 'ADC')
        self.filtered_plot.setLabel('bottom', 'Tiempo', 'muestras')
        self.filtered_curve = self.filtered_plot.plot(pen='r', name='Filtered')
        
        layout.addWidget(self.raw_plot)
        layout.addWidget(self.filtered_plot)
        
        return panel
    
    def update_plots(self):
        if len(self.plot_data_raw) > 0:
            self.raw_curve.setData(self.plot_data_raw)
        if len(self.plot_data_filtered) > 0:
            self.filtered_curve.setData(self.plot_data_filtered)
    
    def add_data_point(self, raw_value, filtered_value):
        self.plot_data_raw.append(raw_value)
        self.plot_data_filtered.append(filtered_value)
        
        # Mantener solo los últimos max_points
        if len(self.plot_data_raw) > self.max_points:
            self.plot_data_raw.pop(0)
        if len(self.plot_data_filtered) > self.max_points:
            self.plot_data_filtered.pop(0)
    
    def log_message(self, message):
        self.log_text.append(f"{message}")
        # Mantener solo las últimas 100 líneas
        if self.log_text.document().lineCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.deleteChar()
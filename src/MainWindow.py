from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QLabel, QGroupBox, 
                               QCheckBox, QDoubleSpinBox, QSpinBox, QTextEdit,
                               QSplitter, QFrame, QProgressBar)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMG Real-Time Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Variables para gráficos con tiempo
        self.plot_times = []  # Tiempos en milisegundos desde inicio
        self.plot_data_raw = []
        self.plot_data_filtered = []
        self.max_points = 1000
        self.start_time = None  # Se inicializa cuando empiece la adquisición
        
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
        
        # Calibración EMG
        calibration_group = QGroupBox("Calibración EMG")
        calibration_layout = QVBoxLayout(calibration_group)
        
        # Línea para duración de calibración y botón
        calib_control_layout = QHBoxLayout()
        
        calib_control_layout.addWidget(QLabel("Duración:"))
        self.calibration_duration = QSpinBox()
        self.calibration_duration.setRange(1, 30)
        self.calibration_duration.setValue(5)
        self.calibration_duration.setSuffix(" seg")
        calib_control_layout.addWidget(self.calibration_duration)
        
        self.calibrate_btn = QPushButton("Calibrar")
        calib_control_layout.addWidget(self.calibrate_btn)
        
        calibration_layout.addLayout(calib_control_layout)
        
        # Progreso y estado de calibración
        self.calibration_progress = QProgressBar()
        self.calibration_progress.setVisible(False)
        calibration_layout.addWidget(self.calibration_progress)
        
        self.calibration_status = QLabel("Sin calibrar")
        calibration_layout.addWidget(self.calibration_status)
        
        # Visualización
        visualization_group = QGroupBox("Visualización")
        visualization_layout = QVBoxLayout(visualization_group)
        
        self.show_raw_check = QCheckBox("Mostrar señal cruda")
        self.show_raw_check.setChecked(False)  # Desactivado por defecto
        self.show_raw_check.toggled.connect(self.toggle_raw_plot)
        
        visualization_layout.addWidget(self.show_raw_check)
        
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
        layout.addWidget(calibration_group)
        layout.addWidget(visualization_group)
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
        
        # Gráfico de señal cruda (valores RAW del ADS1115)
        self.raw_plot = pg.PlotWidget(title="Señal Cruda (RAW)")
        self.raw_plot.setLabel('left', 'Valor RAW', 'ADC')
        self.raw_plot.setLabel('bottom', 'Tiempo', 'ms')
        self.raw_curve = self.raw_plot.plot(pen='b', name='Raw')
        self.raw_plot.setVisible(False)  # Oculto por defecto
        
        # Gráfico de potencial muscular (en µV)
        self.filtered_plot = pg.PlotWidget(title="Potencial Muscular EMG")
        self.filtered_plot.setLabel('left', 'Potencial', 'µV')
        self.filtered_plot.setLabel('bottom', 'Tiempo', 'ms')
        self.filtered_curve = self.filtered_plot.plot(pen='r', name='EMG µV')
        
        layout.addWidget(self.raw_plot)
        layout.addWidget(self.filtered_plot)
        
        return panel
    
    def reset_time_reference(self):
        """Reinicia el tiempo de referencia cuando empiece la adquisición"""
        self.start_time = time.time() * 1000  # Tiempo en milisegundos
        self.plot_times.clear()
        self.plot_data_raw.clear()
        self.plot_data_filtered.clear()
    
    def toggle_raw_plot(self, checked):
        self.raw_plot.setVisible(checked)
    
    def update_plots(self):
        if len(self.plot_times) > 0:
            if self.show_raw_check.isChecked() and len(self.plot_data_raw) > 0:
                self.raw_curve.setData(self.plot_times, self.plot_data_raw)
            if len(self.plot_data_filtered) > 0:
                self.filtered_curve.setData(self.plot_times, self.plot_data_filtered)
    
    def add_data_point(self, raw_value, muscle_potential_uv):
        # Calcular tiempo transcurrido en milisegundos
        if self.start_time is None:
            self.reset_time_reference()
        
        current_time_ms = (time.time() * 1000) - self.start_time
        
        self.plot_times.append(current_time_ms)
        self.plot_data_raw.append(raw_value)
        self.plot_data_filtered.append(muscle_potential_uv)
        
        # Mantener solo los últimos max_points
        if len(self.plot_times) > self.max_points:
            self.plot_times.pop(0)
            self.plot_data_raw.pop(0)
            self.plot_data_filtered.pop(0)
    
    def update_calibration_progress(self, progress):
        """Actualiza la barra de progreso de calibración (0.0 a 1.0)"""
        self.calibration_progress.setValue(int(progress * 100))
    
    def set_calibration_state(self, calibrating):
        """Cambia el estado visual de calibración"""
        if calibrating:
            self.calibration_progress.setVisible(True)
            self.calibration_progress.setValue(0)
            self.calibrate_btn.setText("Calibrando...")
            self.calibrate_btn.setEnabled(False)
            self.calibration_status.setText("Calibrando - manténgase en reposo")
        else:
            self.calibration_progress.setVisible(False)
            self.calibrate_btn.setText("Calibrar")
            self.calibrate_btn.setEnabled(True)
    
    def set_calibration_result(self, success, offset_mv=0.0):
        """Muestra el resultado de la calibración"""
        if success:
            self.calibration_status.setText(f"Calibrado (offset: {offset_mv:.1f}mV)")
        else:
            self.calibration_status.setText("Error en calibración")
    
    def log_message(self, message):
        self.log_text.append(f"{message}")
        # Mantener solo las últimas 100 líneas
        if self.log_text.document().lineCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.deleteChar()
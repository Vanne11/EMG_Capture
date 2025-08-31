from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QLabel, QGroupBox, 
                               QCheckBox, QDoubleSpinBox, QSpinBox, QTextEdit,
                               QSplitter, QFrame, QProgressBar, QScrollArea)
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
        
        # Configuración de ventana de tiempo dinámica
        self.time_window_ms = 10000  # Por defecto 10 segundos
        self.sample_rate = 100  # Hz - frecuencia de muestreo estimada
        self.max_points = self._calculate_max_points()  # Calcular dinámicamente
        
        self.start_time = None  # Se inicializa cuando empiece la adquisición
        
        # Estado de calibración para ajuste de escala
        self.is_calibrated = False
        
        # Líneas de medición
        self.measurement_lines = []
        self.measurement_labels = []
        
        # Timer para actualización de gráficos
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plots)
        self.plot_timer.start(50)  # Actualizar cada 50ms
        
        self.setup_ui()
    
    def _calculate_max_points(self):
        """Calcula la cantidad máxima de puntos basándose en la ventana de tiempo"""
        # Agregar 50% extra para tener buffer adicional
        points_needed = int((self.time_window_ms / 1000) * self.sample_rate * 1.5)
        # Mínimo 500 puntos, máximo 5000 para rendimiento
        return max(500, min(5000, points_needed))
    
    def _update_max_points(self):
        """Actualiza max_points y ajusta los buffers de datos"""
        old_max_points = self.max_points
        self.max_points = self._calculate_max_points()
        
        # Si aumentó la capacidad, no necesitamos hacer nada (los datos se acumularán)
        # Si disminuyó, recortar los datos más antiguos
        if self.max_points < old_max_points:
            if len(self.plot_times) > self.max_points:
                excess = len(self.plot_times) - self.max_points
                self.plot_times = self.plot_times[excess:]
                self.plot_data_raw = self.plot_data_raw[excess:]
                self.plot_data_filtered = self.plot_data_filtered[excess:]
        
        # Log del cambio para debug
        print(f"Max points actualizado: {old_max_points} -> {self.max_points} (ventana: {self.time_window_ms/1000}s)")
        
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
        panel.setFixedWidth(350)  # Ancho fijo para evitar estiramientos
        
        # Crear un scroll area para todo el panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contenedor para el scroll
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(10)  # Espaciado consistente
        
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
        
        # Selector de ventana de tiempo
        time_window_layout = QHBoxLayout()
        time_window_layout.addWidget(QLabel("Ventana:"))
        
        self.time_window_combo = QComboBox()
        self.time_window_combo.addItems(["5 seg", "10 seg", "15 seg", "20 seg", "30 seg", "60 seg", "120 seg"])
        self.time_window_combo.setCurrentText("10 seg")  # Por defecto 10 segundos
        self.time_window_combo.currentTextChanged.connect(self.update_time_window)
        
        time_window_layout.addWidget(self.time_window_combo)
        
        visualization_layout.addWidget(self.show_raw_check)
        visualization_layout.addLayout(time_window_layout)
        
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
        
        # Transmisión Web
        web_transmission_group = QGroupBox("Transmisión Web")
        web_transmission_layout = QVBoxLayout(web_transmission_group)
        
        self.web_transmission_btn = QPushButton("Iniciar Transmisión Web")
        self.web_transmission_status = QLabel("Transmisión detenida")
        self.clear_server_btn = QPushButton("Limpiar Datos Servidor")
        
        web_transmission_layout.addWidget(self.web_transmission_btn)
        web_transmission_layout.addWidget(self.web_transmission_status)
        web_transmission_layout.addWidget(self.clear_server_btn)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        # Agregar grupos al panel con espaciado consistente
        layout.addWidget(serial_group)
        layout.addWidget(acquisition_group)
        layout.addWidget(calibration_group)
        layout.addWidget(visualization_group)
        layout.addWidget(filters_group)
        layout.addWidget(recording_group)
        layout.addWidget(websocket_group)
        layout.addWidget(web_transmission_group)
        layout.addWidget(log_group)
        layout.addStretch()
        
        # Configurar el scroll area
        scroll_area.setWidget(scroll_widget)
        
        # Layout principal del panel
        main_panel_layout = QVBoxLayout(panel)
        main_panel_layout.setContentsMargins(0, 0, 0, 0)
        main_panel_layout.addWidget(scroll_area)
        
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
        
        # Configurar escalas fijas iniciales (antes de calibrar)
        self.filtered_plot.setYRange(-50, 3000, padding=0)
        
        # Deshabilitar todas las interacciones del mouse
        self.raw_plot.setMouseEnabled(x=False, y=False)
        self.filtered_plot.setMouseEnabled(x=False, y=False)
        
        # Deshabilitar menú contextual
        self.raw_plot.setMenuEnabled(False)
        self.filtered_plot.setMenuEnabled(False)
        
        # Bloquear completamente las interacciones
        self.raw_plot.getViewBox().setMouseEnabled(x=False, y=False)
        self.filtered_plot.getViewBox().setMouseEnabled(x=False, y=False)
        
        # Deshabilitar autoRange
        self.raw_plot.enableAutoRange(enable=False)
        self.filtered_plot.enableAutoRange(enable=False)
        
        # Agregar líneas de medición
        self.add_measurement_lines()
        
        layout.addWidget(self.raw_plot)
        layout.addWidget(self.filtered_plot)
        
        return panel
    
    def add_measurement_lines(self):
        """Agrega tres líneas horizontales de medición con diferentes colores"""
        colors = ['#FF0000', '#00AA00', '#0066FF']  # Rojo, Verde oscuro, Azul oscuro
        initial_positions = [100, 500, 1000]  # Posiciones iniciales en µV
        
        for i, (color, pos) in enumerate(zip(colors, initial_positions)):
            # Crear línea infinita horizontal
            line = pg.InfiniteLine(
                pos=pos,
                angle=0,  # Horizontal
                pen=pg.mkPen(color=color, width=2),
                movable=True,
                bounds=None
            )
            
            # Configurar la línea para que solo se mueva verticalmente
            line.sigPositionChangeFinished.connect(lambda line=line, idx=i: self.update_measurement_label(line, idx))
            
            # Agregar al gráfico
            self.filtered_plot.addItem(line)
            self.measurement_lines.append(line)
            
            # Crear label para mostrar el valor con fondo sólido
            label = pg.TextItem(
                text=f'{pos:.1f} µV',
                color='#000000',  # Texto negro para mejor contraste
                anchor=(0, 0.5),
                border=pg.mkPen(color=color, width=2),
                fill=pg.mkBrush(255, 255, 255, 255)  # Fondo blanco sólido
            )
            
            # Posicionar el label al lado derecho
            self.filtered_plot.addItem(label)
            self.measurement_labels.append(label)
            
            # Actualizar posición inicial del label
            self.update_measurement_label(line, i)
    
    def update_measurement_label(self, line, index):
        """Actualiza la posición y texto del label de medición"""
        if index < len(self.measurement_labels):
            # Obtener posición actual de la línea
            pos_y = line.value()
            
            # Actualizar texto del label
            self.measurement_labels[index].setText(f'{pos_y:.1f} µV')
            
            # Posicionar label más hacia la izquierda para que se vea completo
            view_range = self.filtered_plot.getViewBox().viewRange()
            x_range = view_range[0][1] - view_range[0][0]
            x_right = view_range[0][1] - (x_range * 0.15)  # 15% desde el borde derecho (más espacio)
            
            self.measurement_labels[index].setPos(x_right, pos_y)
    
    def reset_time_reference(self):
        """Reinicia el tiempo de referencia cuando empiece la adquisición"""
        self.start_time = time.time() * 1000  # Tiempo en milisegundos
        self.plot_times.clear()
        self.plot_data_raw.clear()
        self.plot_data_filtered.clear()
    
    def toggle_raw_plot(self, checked):
        self.raw_plot.setVisible(checked)
    
    def update_time_window(self, text):
        """Actualiza la ventana de tiempo según la selección"""
        time_map = {
            "5 seg": 5000,
            "10 seg": 10000,
            "15 seg": 15000,
            "20 seg": 20000,
            "30 seg": 30000,
            "60 seg": 60000,
            "120 seg": 120000
        }
        
        old_window = self.time_window_ms
        self.time_window_ms = time_map.get(text, 10000)
        
        # Actualizar max_points basándose en la nueva ventana
        self._update_max_points()
        
        # Actualizar labels cuando cambie la ventana de tiempo
        self.update_all_measurement_labels()
        
        # Log del cambio
        self.log_message(f"Ventana de tiempo cambiada: {old_window/1000}s -> {self.time_window_ms/1000}s (buffer: {self.max_points} puntos)")
    
    def update_all_measurement_labels(self):
        """Actualiza la posición de todos los labels de medición"""
        for i, line in enumerate(self.measurement_lines):
            self.update_measurement_label(line, i)
    
    def update_plots(self):
        if len(self.plot_times) > 0:
            # Actualizar gráfico crudo si está visible
            if self.show_raw_check.isChecked() and len(self.plot_data_raw) > 0:
                self.raw_curve.setData(self.plot_times, self.plot_data_raw)
                
            # Actualizar gráfico filtrado con ventana deslizante
            if len(self.plot_data_filtered) > 0:
                self.filtered_curve.setData(self.plot_times, self.plot_data_filtered)
                
                # Configurar ventana deslizante con tiempo configurable
                current_time = self.plot_times[-1]
                window_start = current_time - self.time_window_ms
                self.filtered_plot.setXRange(window_start, current_time, padding=0)
                
                # Ajustar escala Y dinámicamente después de calibrar
                if self.is_calibrated:
                    # Solo ajustar si tenemos suficientes datos
                    if len(self.plot_data_filtered) >= 100:
                        # Obtener datos visibles en la ventana de tiempo actual
                        visible_indices = [i for i, t in enumerate(self.plot_times) if t >= window_start]
                        if visible_indices:
                            visible_data = [self.plot_data_filtered[i] for i in visible_indices]
                            
                            if visible_data:
                                min_val = min(visible_data)
                                max_val = max(visible_data)
                                
                                # Asegurar un rango mínimo razonable
                                range_val = max_val - min_val
                                if range_val < 50:  # Rango mínimo de 50 µV
                                    center = (min_val + max_val) / 2
                                    min_val = center - 25
                                    max_val = center + 25
                                
                                # Aplicar margen del 20%
                                margin = range_val * 0.2
                                y_min = min_val - margin
                                y_max = max_val + margin
                                
                                self.filtered_plot.setYRange(y_min, y_max, padding=0)
                
                # Actualizar posiciones de los labels de medición
                self.update_all_measurement_labels()
    
    def add_data_point(self, raw_value, muscle_potential_uv):
        # Calcular tiempo transcurrido en milisegundos
        if self.start_time is None:
            self.reset_time_reference()
        
        current_time_ms = (time.time() * 1000) - self.start_time
        
        self.plot_times.append(current_time_ms)
        self.plot_data_raw.append(raw_value)
        self.plot_data_filtered.append(muscle_potential_uv)
        
        # Mantener solo los últimos max_points (ahora dinámico)
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
            # Mantener escala fija durante calibración
            self.filtered_plot.setYRange(-50, 3000, padding=0)
        else:
            self.calibration_progress.setVisible(False)
            self.calibrate_btn.setText("Calibrar")
            self.calibrate_btn.setEnabled(True)
    
    def set_calibration_result(self, success, offset_mv=0.0):
        """Muestra el resultado de la calibración"""
        if success:
            self.calibration_status.setText(f"Calibrado (offset: {offset_mv:.1f}mV)")
            self.is_calibrated = True  # Activar ajuste automático de escala
            # Forzar actualización del layout después de calibrar
            self.filtered_plot.getViewBox().updateViewRange()
        else:
            self.calibration_status.setText("Error en calibración")
            self.is_calibrated = False
    
    def log_message(self, message):
        self.log_text.append(f"{message}")
        # Mantener solo las últimas 100 líneas
        if self.log_text.document().lineCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.deleteChar()
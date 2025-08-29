import numpy as np
from scipy import signal
from collections import deque

class SignalProcessor:
    def __init__(self, sample_rate=100):
        self.sample_rate = sample_rate
        self.buffer_size = 1000
        self.data_buffer = deque(maxlen=self.buffer_size)
        
        # Parámetros de filtros
        self.lowpass_cutoff = 30.0
        self.highpass_cutoff = 0.5
        self.notch_freq = 50.0
        self.moving_avg_window = 10
        
        # Estados de filtros
        self.active_filters = {
            'lowpass': False,
            'highpass': False,
            'notch': False,
            'moving_avg': False
        }
        
        # Buffer para promedio móvil
        self.moving_avg_buffer = deque(maxlen=self.moving_avg_window)
        
        # Parámetros de conversión EMG
        self.ads_resolution = 0.1875  # mV por LSB (ADS1115 con ganancia 2/3)
        self.system_gain = 1200.0     # Ganancia estimada del sistema
        
        # Calibración
        self.is_calibrating = False
        self.calibration_samples = []
        self.calibration_target_count = 500  # Por defecto 5 segundos
        self.baseline_offset_mv = 0.0  # Offset en mV
        self.is_calibrated = False
        
    def add_sample(self, raw_value):
        """Procesa una muestra RAW del ADS1115 y devuelve el potencial muscular en µV"""
        
        # Convertir RAW a mV (salida del sistema de amplificación)
        voltage_mv = raw_value * self.ads_resolution
        
        # Si estamos calibrando, almacenar muestra
        if self.is_calibrating:
            self.calibration_samples.append(voltage_mv)
            if len(self.calibration_samples) >= self.calibration_target_count:
                self.finish_calibration()
            return 0.0  # Durante calibración devolver 0 µV
        
        # Convertir a potencial muscular original en µV
        if self.is_calibrated:
            muscle_potential_uv = ((voltage_mv - self.baseline_offset_mv) / self.system_gain) * 1000
        else:
            # Sin calibrar, asumir offset de 666mV (valor típico observado)
            muscle_potential_uv = ((voltage_mv - 666.0) / self.system_gain) * 1000
        
        # Agregar al buffer para filtros
        self.data_buffer.append(muscle_potential_uv)
        
        # Aplicar filtros al potencial muscular
        return self.apply_filters(muscle_potential_uv)
    
    def start_calibration(self, duration_seconds=5):
        """Inicia el proceso de calibración"""
        self.calibration_target_count = int(duration_seconds * self.sample_rate)
        self.calibration_samples = []
        self.is_calibrating = True
        self.is_calibrated = False
        return True
    
    def finish_calibration(self):
        """Finaliza la calibración y calcula el offset baseline"""
        if len(self.calibration_samples) > 0:
            self.baseline_offset_mv = np.mean(self.calibration_samples)
            self.is_calibrated = True
            self.is_calibrating = False
            return True, self.baseline_offset_mv
        return False, 0.0
    
    def get_calibration_progress(self):
        """Retorna el progreso de calibración (0.0 a 1.0)"""
        if not self.is_calibrating:
            return 0.0
        return len(self.calibration_samples) / self.calibration_target_count
    
    def set_system_gain(self, gain):
        """Permite ajustar la ganancia del sistema si se conoce"""
        self.system_gain = float(gain)
    
    def apply_filters(self, value):
        filtered_value = value
        
        # Filtro promedio móvil (aplicar primero)
        if self.active_filters['moving_avg']:
            filtered_value = self._moving_average_filter(filtered_value)
        
        # Para filtros IIR necesitamos suficientes muestras
        if len(self.data_buffer) < 10:
            return filtered_value
            
        # Aplicar filtros digitales
        data_array = np.array(list(self.data_buffer))
        
        if self.active_filters['notch']:
            data_array = self._notch_filter(data_array)
            
        if self.active_filters['lowpass']:
            data_array = self._lowpass_filter(data_array)
            
        if self.active_filters['highpass']:
            data_array = self._highpass_filter(data_array)
        
        return data_array[-1]  # Retornar último valor filtrado
    
    def _moving_average_filter(self, value):
        self.moving_avg_buffer.append(value)
        return sum(self.moving_avg_buffer) / len(self.moving_avg_buffer)
    
    def _lowpass_filter(self, data):
        nyquist = self.sample_rate / 2
        normal_cutoff = self.lowpass_cutoff / nyquist
        b, a = signal.butter(2, normal_cutoff, btype='low', analog=False)
        return signal.filtfilt(b, a, data)
    
    def _highpass_filter(self, data):
        nyquist = self.sample_rate / 2
        normal_cutoff = self.highpass_cutoff / nyquist
        b, a = signal.butter(2, normal_cutoff, btype='high', analog=False)
        return signal.filtfilt(b, a, data)
    
    def _notch_filter(self, data):
        nyquist = self.sample_rate / 2
        normal_freq = self.notch_freq / nyquist
        b, a = signal.iirnotch(normal_freq, 30.0)
        return signal.filtfilt(b, a, data)
    
    def set_filter_state(self, filter_type, active):
        if filter_type in self.active_filters:
            self.active_filters[filter_type] = active
    
    def set_filter_params(self, **kwargs):
        if 'lowpass_cutoff' in kwargs:
            self.lowpass_cutoff = kwargs['lowpass_cutoff']
        if 'highpass_cutoff' in kwargs:
            self.highpass_cutoff = kwargs['highpass_cutoff']
        if 'notch_freq' in kwargs:
            self.notch_freq = kwargs['notch_freq']
        if 'moving_avg_window' in kwargs:
            self.moving_avg_window = kwargs['moving_avg_window']
            self.moving_avg_buffer = deque(maxlen=self.moving_avg_window)
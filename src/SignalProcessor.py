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
        
    def add_sample(self, value):
        self.data_buffer.append(value)
        return self.apply_filters(value)
    
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
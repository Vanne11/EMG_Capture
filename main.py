#!/usr/bin/env python3
"""
EMG Real-Time Monitor
Aplicación para monitoreo en tiempo real de señales EMG
"""

import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from EMGApplication import main

if __name__ == "__main__":
    main()
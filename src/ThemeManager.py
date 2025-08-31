from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
import pyqtgraph as pg

# Variable interna para seleccionar tema
CURRENT_THEME = "dark"  # Cambiar a "light" para tema claro

class ThemeManager:
    def __init__(self):
        # Tema Oscuro - Paleta morados
        self.dark_theme = {
            'primary': '#4b1c71',      # Morado oscuro
            'secondary': '#7f4ca5',    # Morado medio
            'accent': '#b57edc',       # Morado claro
            'background': '#dbb6ee',   # Morado muy claro
            'surface': '#fff0ff',      # Blanco rosado
            'text_primary': '#ffffff',
            'text_secondary': '#e0e0e0',
            'text_on_light': '#4b1c71',
            'border': '#7f4ca5',
            'button': '#7f4ca5',
            'button_hover': '#b57edc',
            'input': '#dbb6ee',
            'plot_bg': '#4b1c71',
            'plot_grid': '#7f4ca5',
            'plot_curve': '#b57edc',
            'label_text': '#000000'    # Letra negra para labels
        }
        
        # Tema Claro - Paleta pasteles
        self.light_theme = {
            'primary': '#ffe4e1',      # Rosa muy claro
            'secondary': '#d8f8e1',    # Verde muy claro
            'accent': '#fcb7af',       # Coral claro
            'background': '#b0f2c2',   # Verde claro
            'surface': '#b0c2f2',      # Azul claro
            'text_primary': '#333333',
            'text_secondary': '#666666',
            'text_on_light': '#333333',
            'border': '#b0c2f2',
            'button': '#fcb7af',
            'button_hover': '#d8f8e1',
            'input': '#ffffff',
            'plot_bg': '#ffffff',
            'plot_grid': '#d8f8e1',
            'plot_curve': '#0066CC',   # Azul más oscuro para mejor contraste
            'label_text': '#000000'    # Letra negra para labels
        }
        
        self.current_colors = self.dark_theme if CURRENT_THEME == "dark" else self.light_theme
    
    def get_current_theme(self):
        """Retorna el tema actual"""
        return CURRENT_THEME
    
    def get_color(self, color_name):
        """Obtiene un color específico del tema actual"""
        return self.current_colors.get(color_name, '#000000')
    
    def apply_theme_to_application(self, app):
        """Aplica el tema a toda la aplicación"""
        palette = QPalette()
        
        if CURRENT_THEME == "dark":
            # Configuración para tema oscuro
            palette.setColor(QPalette.Window, QColor(self.get_color('primary')))
            palette.setColor(QPalette.WindowText, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.Base, QColor(self.get_color('background')))
            palette.setColor(QPalette.AlternateBase, QColor(self.get_color('secondary')))
            palette.setColor(QPalette.ToolTipBase, QColor(self.get_color('surface')))
            palette.setColor(QPalette.ToolTipText, QColor(self.get_color('text_on_light')))
            palette.setColor(QPalette.Text, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.Button, QColor(self.get_color('button')))
            palette.setColor(QPalette.ButtonText, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.BrightText, QColor(self.get_color('accent')))
            palette.setColor(QPalette.Link, QColor(self.get_color('accent')))
            palette.setColor(QPalette.Highlight, QColor(self.get_color('accent')))
            palette.setColor(QPalette.HighlightedText, QColor(self.get_color('text_on_light')))
        else:
            # Configuración para tema claro
            palette.setColor(QPalette.Window, QColor(self.get_color('primary')))
            palette.setColor(QPalette.WindowText, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.Base, QColor(self.get_color('input')))
            palette.setColor(QPalette.AlternateBase, QColor(self.get_color('secondary')))
            palette.setColor(QPalette.ToolTipBase, QColor(self.get_color('surface')))
            palette.setColor(QPalette.ToolTipText, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.Text, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.Button, QColor(self.get_color('button')))
            palette.setColor(QPalette.ButtonText, QColor(self.get_color('text_primary')))
            palette.setColor(QPalette.BrightText, QColor(self.get_color('accent')))
            palette.setColor(QPalette.Link, QColor(self.get_color('accent')))
            palette.setColor(QPalette.Highlight, QColor(self.get_color('accent')))
            palette.setColor(QPalette.HighlightedText, QColor(self.get_color('text_primary')))
        
        app.setPalette(palette)
    
    def apply_theme_to_plots(self, raw_plot, filtered_plot):
        """Aplica el tema a los gráficos de pyqtgraph"""
        # Configurar fondo de los plots
        raw_plot.setBackground(self.get_color('plot_bg'))
        filtered_plot.setBackground(self.get_color('plot_bg'))
        
        # Configurar colores de ejes y grillas
        axis_color = self.get_color('text_primary') if CURRENT_THEME == "dark" else self.get_color('text_primary')
        grid_color = self.get_color('plot_grid')
        
        # Aplicar estilos a ejes del gráfico crudo
        for axis_name in ['left', 'bottom']:
            axis = raw_plot.getAxis(axis_name)
            axis.setPen(pg.mkPen(color=axis_color, width=1))
            axis.setTextPen(pg.mkPen(color=axis_color))
        
        # Aplicar estilos a ejes del gráfico filtrado
        for axis_name in ['left', 'bottom']:
            axis = filtered_plot.getAxis(axis_name)
            axis.setPen(pg.mkPen(color=axis_color, width=1))
            axis.setTextPen(pg.mkPen(color=axis_color))
        
        # Configurar grillas
        raw_plot.showGrid(x=True, y=True, alpha=0.3)
        filtered_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Actualizar color de las curvas
        return {
            'raw_curve_color': 'b' if CURRENT_THEME == "dark" else self.get_color('plot_curve'),
            'filtered_curve_color': self.get_color('plot_curve')
        }
    
    def get_widget_stylesheet(self):
        """Retorna stylesheet CSS para widgets específicos"""
        if CURRENT_THEME == "dark":
            return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.get_color('border')};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: {self.get_color('secondary')};
                color: {self.get_color('text_primary')};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.get_color('text_primary')};
            }}
            QPushButton {{
                background-color: {self.get_color('button')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 6px;
                color: {self.get_color('text_primary')};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.get_color('button_hover')};
            }}
            QPushButton:pressed {{
                background-color: {self.get_color('accent')};
            }}
            QPushButton:disabled {{
                background-color: {self.get_color('secondary')};
                color: {self.get_color('text_secondary')};
            }}
            QComboBox {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 4px;
                color: {self.get_color('text_on_light')};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 4px;
                color: {self.get_color('text_on_light')};
            }}
            QTextEdit {{
                background-color: {self.get_color('surface')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                color: {self.get_color('text_on_light')};
            }}
            QProgressBar {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.get_color('accent')};
                border-radius: 3px;
            }}
            QCheckBox {{
                color: {self.get_color('text_primary')};
            }}
            QLabel {{
                color: {self.get_color('text_primary')};
                background-color: transparent !important;
                background: none !important;
            }}
            QFrame {{
                background-color: {self.get_color('primary')};
            }}
            """
        else:
            return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {self.get_color('border')};
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: {self.get_color('secondary')};
                color: {self.get_color('text_primary')};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.get_color('text_primary')};
            }}
            QPushButton {{
                background-color: {self.get_color('button')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 6px;
                color: {self.get_color('text_primary')};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.get_color('button_hover')};
            }}
            QPushButton:pressed {{
                background-color: {self.get_color('accent')};
            }}
            QPushButton:disabled {{
                background-color: {self.get_color('surface')};
                color: {self.get_color('text_secondary')};
            }}
            QComboBox {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 4px;
                color: {self.get_color('text_primary')};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                padding: 4px;
                color: {self.get_color('text_primary')};
            }}
            QTextEdit {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                color: {self.get_color('text_primary')};
            }}
            QProgressBar {{
                background-color: {self.get_color('input')};
                border: 1px solid {self.get_color('border')};
                border-radius: 4px;
                text-align: center;
                color: {self.get_color('text_primary')};
            }}
            QProgressBar::chunk {{
                background-color: {self.get_color('accent')};
                border-radius: 3px;
            }}
            QCheckBox {{
                color: {self.get_color('text_primary')};
            }}
            QLabel {{
                color: {self.get_color('text_primary')};
                background-color: transparent !important;
                background: none !important;
            }}
            QFrame {{
                background-color: {self.get_color('primary')};
            }}
            """
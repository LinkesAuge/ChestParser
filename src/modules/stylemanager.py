# stylemanager.py - StyleManager class implementation
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

# Style constants
DARK_THEME = {
    'background': '#1A2742',  # Dark blue background similar to Total Battle
    'foreground': '#FFFFFF',  # White text for better contrast
    'accent': '#D4AF37',      # Gold accent for lines and small highlights
    'accent_hover': '#F0C75A',  # Lighter gold for hover states
    'background_light': '#2A3752',  # Slightly lighter background for cards
    'background_secondary': '#2A3752',  # Secondary background color
    'card_bg': '#0D1A33',     # Darker blue for card backgrounds
    'border': '#2A3F5F',      # Medium blue for borders
    'text': '#FFFFFF',        # Primary text color
    'text_secondary': '#8899AA',  # Secondary text color
    'text_disabled': '#8899AA',  # Disabled text color
    'header_bg': '#0E2145',   # Header background
    'button_gradient_start': '#1A3863',  # Top gradient for buttons
    'button_gradient_end': '#0B1A36',  # Bottom gradient for buttons
    'button_hover_gradient_start': '#D4AF37',  # Gold gradient top for hover
    'button_hover_gradient_end': '#B28E1C',  # Gold gradient bottom for hover
    'button_pressed': '#A37F18',  # Button pressed state
    'button_disabled': '#5A6A7A',  # Disabled button color
    'selection_bg': '#D4AF37',  # Selection background
    'selection_inactive_bg': '#2A3752',  # Selection background when inactive
    'warning': '#f28e2c',     # Warning color
    'info': '#76b7b2',        # Info color
    'success': '#56A64B',     # Success color
    'error': '#A6564B'        # Error color
}

class StyleManager:
    """Manage application styling and themes."""
    
    @staticmethod
    def apply_dark_theme(app):
        """Apply dark theme to the application."""
        app.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
            }}
            
            QWidget {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
            }}
            
            QLabel {{
                color: {DARK_THEME['foreground']};
                background: transparent;
            }}
            
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_THEME['button_gradient_start']},
                    stop:1 {DARK_THEME['button_gradient_end']});
                border: 1px solid {DARK_THEME['border']};
                border-radius: 3px;
                color: {DARK_THEME['foreground']};
                padding: 5px 15px;
                min-height: 25px;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_THEME['button_hover_gradient_start']},
                    stop:1 {DARK_THEME['button_hover_gradient_end']});
                border-color: {DARK_THEME['accent']};
            }}
            
            QPushButton:pressed {{
                background: {DARK_THEME['button_pressed']};
            }}
            
            QPushButton:disabled {{
                background: {DARK_THEME['button_disabled']};
                color: {DARK_THEME['text_disabled']};
                border-color: {DARK_THEME['border']};
            }}
            
            QLineEdit, QComboBox, QSpinBox, QDateEdit {{
                background-color: {DARK_THEME['background_light']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 3px;
                color: {DARK_THEME['foreground']};
                padding: 5px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                border-color: {DARK_THEME['accent']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: url(resources/icons/down_arrow.png);
                width: 12px;
                height: 12px;
            }}
            
            QTableView {{
                background-color: {DARK_THEME['background_light']};
                alternate-background-color: {DARK_THEME['card_bg']};
                border: 1px solid {DARK_THEME['border']};
                gridline-color: {DARK_THEME['border']};
                selection-background-color: {DARK_THEME['selection_bg']};
                selection-color: {DARK_THEME['foreground']};
            }}
            
            QHeaderView::section {{
                background-color: {DARK_THEME['header_bg']};
                color: {DARK_THEME['foreground']};
                padding: 5px;
                border: 1px solid {DARK_THEME['border']};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {DARK_THEME['border']};
                background-color: {DARK_THEME['background']};
            }}
            
            QTabBar::tab {{
                background-color: {DARK_THEME['background_light']};
                color: {DARK_THEME['foreground']};
                padding: 8px 20px;
                border: 1px solid {DARK_THEME['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {DARK_THEME['background']};
                border-bottom: 2px solid {DARK_THEME['accent']};
            }}
            
            QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            
            QGroupBox {{
                border: 2px solid {DARK_THEME['accent']};
                border-radius: 5px;
                margin-top: 1em;
                padding: 10px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: {DARK_THEME['accent']};
            }}
            
            QListWidget {{
                background-color: {DARK_THEME['background_light']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 3px;
            }}
            
            QListWidget::item {{
                color: {DARK_THEME['foreground']};
                padding: 5px;
            }}
            
            QListWidget::item:selected {{
                background-color: {DARK_THEME['selection_bg']};
                color: {DARK_THEME['foreground']};
            }}
            
            QListWidget::item:hover {{
                background-color: {DARK_THEME['selection_inactive_bg']};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {DARK_THEME['background']};
                width: 14px;
                margin: 15px 0 15px 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {DARK_THEME['background_light']};
                min-height: 30px;
                border-radius: 7px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {DARK_THEME['accent']};
            }}
            
            QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 15px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }}
            
            QScrollBar::add-line:vertical {{
                border: none;
                background: none;
                height: 15px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }}
            
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                border: none;
                width: 10px;
                height: 10px;
                background: none;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QStatusBar {{
                background-color: {DARK_THEME['header_bg']};
                color: {DARK_THEME['foreground']};
            }}
            
            QCheckBox {{
                color: {DARK_THEME['foreground']};
            }}
            
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
            }}
            
            QCheckBox::indicator:unchecked {{
                border: 1px solid {DARK_THEME['border']};
                background-color: {DARK_THEME['background_light']};
            }}
            
            QCheckBox::indicator:checked {{
                border: 1px solid {DARK_THEME['accent']};
                background-color: {DARK_THEME['accent']};
            }}
        """)


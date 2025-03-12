# stylemanager.py - StyleManager class implementation
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

# Style constants
DARK_THEME = {
    'background': '#0E1629',          # Darker blue background for better contrast
    'foreground': '#FFFFFF',          # White text for better contrast
    'accent': '#D4AF37',              # Gold accent for highlights and borders
    'accent_hover': '#F0C75A',        # Lighter gold for hover states
    'background_light': '#1A2742',    # Slightly lighter background for cards/controls
    'background_secondary': '#162038', # Secondary background color
    'card_bg': '#0D1A33',             # Darker blue for card backgrounds
    'border': '#2A3F5F',              # Medium blue for borders
    'text': '#FFFFFF',                # Primary text color
    'text_secondary': '#A0B0C0',      # Lighter secondary text for better readability
    'text_disabled': '#8899AA',       # Disabled text color
    'header_bg': '#0A1220',           # Darker header background
    'button_gradient_start': '#1A3863', # Top gradient for buttons
    'button_gradient_end': '#0B1A36',   # Bottom gradient for buttons
    'button_hover_gradient_start': '#D4AF37', # Gold gradient top for hover
    'button_hover_gradient_end': '#B28E1C',   # Gold gradient bottom for hover
    'button_pressed': '#A37F18',      # Button pressed state
    'button_disabled': '#5A6A7A',     # Disabled button color
    'selection_bg': '#2C427A',        # Darker blue for selection background (not gold)
    'selection_text': '#FFFFFF',      # White text for selections
    'selection_inactive_bg': '#1A2742', # Selection background when inactive
    'warning': '#f28e2c',             # Warning color
    'info': '#76b7b2',                # Info color
    'success': '#56A64B',             # Success color
    'error': '#A6564B',               # Error color
    'checkbox_bg': '#0E1629',         # Checkbox background
    'checkbox_border': '#2A3F5F',     # Checkbox border
    'checkbox_checked_bg': '#1A2742', # Checkbox checked background
    'checkbox_check_mark': '#D4AF37'  # Checkbox check mark color (gold)
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
            
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                height: 15px;
            }}
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {DARK_THEME['accent']};
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
                selection-color: {DARK_THEME['selection_text']};
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
                font-weight: bold;
            }}
            
            QListWidget {{
                background-color: {DARK_THEME['background_light']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 3px;
            }}
            
            QListWidget::item {{
                color: {DARK_THEME['foreground']};
                padding: 5px;
                border: none;
            }}
            
            QListWidget::item:selected {{
                background-color: {DARK_THEME['selection_bg']};
                color: {DARK_THEME['selection_text']};
                border: none;
            }}
            
            /* Remove hover effect as requested */
            QListWidget::item:hover {{
                background-color: transparent;
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
            
            /* Improved checkbox styling */
            QCheckBox {{
                color: {DARK_THEME['foreground']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
            }}
            
            QCheckBox::indicator:unchecked {{
                border: 2px solid {DARK_THEME['checkbox_border']};
                background-color: {DARK_THEME['checkbox_bg']};
            }}
            
            QCheckBox::indicator:checked {{
                border: 2px solid {DARK_THEME['accent']};
                background-color: {DARK_THEME['checkbox_checked_bg']};
                /* Draw a gold checkmark using background gradient */
                background-image: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0.4 transparent,
                    stop: 0.41 {DARK_THEME['checkbox_check_mark']},
                    stop: 0.59 {DARK_THEME['checkbox_check_mark']},
                    stop: 0.6 transparent);
                background-image: qlineargradient(x1: 1, y1: 0, x2: 0, y2: 1,
                    stop: 0.4 transparent,
                    stop: 0.41 {DARK_THEME['checkbox_check_mark']},
                    stop: 0.59 {DARK_THEME['checkbox_check_mark']},
                    stop: 0.6 transparent);
            }}
            
            /* Custom styling for the drop area */
            #dropArea {{
                background-color: {DARK_THEME['background_secondary']};
                border: 2px dashed {DARK_THEME['accent']};
                border-radius: 10px;
                padding: 20px;
            }}
            
            /* Style for file input section */
            #fileInputSection {{
                background-color: {DARK_THEME['background_light']};
                border-radius: 8px;
                padding: 15px;
                border: 1px solid {DARK_THEME['border']};
            }}
            
            /* Style for the select file button */
            #selectFileButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_THEME['button_hover_gradient_start']},
                    stop:1 {DARK_THEME['button_hover_gradient_end']});
                border: none;
                border-radius: 5px;
                color: {DARK_THEME['background']};
                padding: 8px 16px;
                font-weight: bold;
                min-height: 30px;
            }}
            
            #selectFileButton:hover {{
                background: {DARK_THEME['accent_hover']};
            }}
        """)


import sys
import os
import csv
import pandas as pd
import numpy as np
import configparser
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
# Configure matplotlib to use PySide6
import matplotlib
matplotlib.use('QtAgg')  # Use the generic Qt backend that works with PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import types  # Add this import for method binding

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QPushButton, QTabWidget, QLabel, QFileDialog,
    QComboBox, QGroupBox, QSplitter, QMessageBox, QFrame, QHeaderView,
    QLineEdit
)
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, Signal, QMimeData, 
    QUrl, QSize, Slot, QSortFilterProxyModel, QObject, QEvent, QTimer,
    QSettings, QStandardPaths
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QDropEvent, QDragEnterEvent,
    QColor, QPalette, QFont, QIcon, QPixmap, QPainter
)

# Style constants
DARK_THEME = {
    'background': '#1A2742',  # Dark blue background similar to Total Battle
    'foreground': '#FFFFFF',  # White text for better contrast
    'accent': '#D4AF37',      # Gold accent color
    'accent_hover': '#F0C75A',  # Lighter gold for hover states
    'secondary': '#345995',   # Secondary blue color
    'success': '#56A64B',     # Keep green for success indicators
    'error': '#A6564B',       # Keep red for error indicators
    'card_bg': '#0D1A33',     # Darker blue for card backgrounds
    'border': '#2A3F5F',      # Medium blue for borders
    'text_disabled': '#8899AA', # Bluish gray for disabled text
    'button_gradient_top': '#D4AF37',    # Gold gradient top for buttons
    'button_gradient_bottom': '#B08A1B', # Darker gold for gradient bottom
    'header_bg': '#0A142A',   # Very dark blue for headers
    'highlight': '#FFDFA0'    # Light gold for highlighted elements
}

class ConfigManager:
    """
    Manages application configuration settings using a config.ini file.
    
    This class handles reading and writing application settings to a configuration file,
    with support for default values and automatic creation of the configuration file
    if it doesn't exist.
    """
    
    def __init__(self, app_name="TotalBattleAnalyzer"):
        """
        Initialize the ConfigManager with the specified app name.
        
        Args:
            app_name (str): The name of the application for configuration purposes.
        """
        self.app_name = app_name
        self.config = configparser.ConfigParser()
        self.config_file = Path("config.ini")
        
        # Create the application directory structure if it doesn't exist
        self.app_dir = Path.cwd()
        self.import_dir = self.app_dir / "import"
        self.export_dir = self.app_dir / "export"
        
        # Create directories if they don't exist
        self.import_dir.mkdir(exist_ok=True)
        self.export_dir.mkdir(exist_ok=True)
        
        # Default settings
        self.default_settings = {
            'General': {
                'theme': 'dark',
                'import_directory': str(self.import_dir),
                'export_directory': str(self.export_dir),
                'last_used_directory': str(self.import_dir),
                'window_width': '1200',
                'window_height': '800'
            },
            'Charts': {
                'default_chart_type': 'Bar Chart',
                'show_grid': 'True',
                'chart_title_size': '14'
            },
            'Data': {
                'default_encoding': 'utf-8',
                'alternative_encodings': 'latin1,iso-8859-1,cp1252,windows-1252,utf-8-sig',
                'csv_separator': ',',
                'alternative_separator': ';',
                'german_encodings': 'latin1,cp1252,iso-8859-1,windows-1252'
            }
        }
        
        # Load or create configuration
        self.load_config()
    
    def load_config(self):
        """
        Load the configuration from the config file.
        If the file doesn't exist, create it with default settings.
        """
        # Check if config file exists
        if self.config_file.exists():
            try:
                self.config.read(self.config_file)
                # Validate sections and options
                self._validate_config()
            except Exception as e:
                print(f"Error loading configuration: {str(e)}")
                # If there's an error, create a new config with defaults
                self._create_default_config()
        else:
            # Create a new config file with defaults
            self._create_default_config()
    
    def _validate_config(self):
        """Validate the loaded configuration and add any missing sections or options."""
        for section, options in self.default_settings.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            for option, value in options.items():
                if not self.config.has_option(section, option):
                    self.config.set(section, option, value)
        
        # Save any added defaults
        self.save_config()
    
    def _create_default_config(self):
        """Create a new configuration file with default settings."""
        for section, options in self.default_settings.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            for option, value in options.items():
                self.config.set(section, option, value)
        
        self.save_config()
    
    def save_config(self):
        """Save the current configuration to the config file."""
        try:
            with open(self.config_file, 'w') as file:
                self.config.write(file)
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
    
    def get(self, section, option, fallback=None):
        """
        Get a configuration value.
        
        Args:
            section (str): The configuration section.
            option (str): The option name within the section.
            fallback (Any): The value to return if the option doesn't exist.
            
        Returns:
            str: The configuration value, or fallback if not found.
        """
        return self.config.get(section, option, fallback=fallback)
    
    def get_int(self, section, option, fallback=0):
        """Get an integer configuration value."""
        return self.config.getint(section, option, fallback=fallback)
    
    def get_float(self, section, option, fallback=0.0):
        """Get a float configuration value."""
        return self.config.getfloat(section, option, fallback=fallback)
    
    def get_boolean(self, section, option, fallback=False):
        """Get a boolean configuration value."""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def set(self, section, option, value):
        """
        Set a configuration value.
        
        Args:
            section (str): The configuration section.
            option (str): The option name within the section.
            value (Any): The value to set (will be converted to string).
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, option, str(value))
        self.save_config()
    
    def get_import_directory(self):
        """Get the configured import directory path."""
        return self.get('General', 'import_directory', str(self.import_dir))
    
    def get_export_directory(self):
        """Get the configured export directory path."""
        return self.get('General', 'export_directory', str(self.export_dir))
    
    def get_last_used_directory(self):
        """Get the last used directory path."""
        return self.get('General', 'last_used_directory', str(self.import_dir))
    
    def set_last_used_directory(self, directory):
        """Set the last used directory path."""
        self.set('General', 'last_used_directory', str(directory))

class StyleManager:
    @staticmethod
    def apply_dark_theme(app):
        """Apply Total Battle-inspired theme to the entire application"""
        dark_palette = QPalette()
        
        # Set colors
        dark_palette.setColor(QPalette.Window, QColor(DARK_THEME['background']))
        dark_palette.setColor(QPalette.WindowText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Base, QColor(DARK_THEME['card_bg']))
        dark_palette.setColor(QPalette.AlternateBase, QColor(DARK_THEME['background']))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.ToolTipText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Text, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Button, QColor(DARK_THEME['card_bg']))
        dark_palette.setColor(QPalette.ButtonText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Link, QColor(DARK_THEME['accent']))
        dark_palette.setColor(QPalette.Highlight, QColor(DARK_THEME['accent']))
        dark_palette.setColor(QPalette.HighlightedText, QColor(DARK_THEME['foreground']))
        
        # Apply theme to the application
        app.setPalette(dark_palette)
        
        # Apply stylesheet for custom styling
        app.setStyleSheet(f"""
            /* Global Styles */
            QWidget {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            /* Main Window */
            QMainWindow {{
                background-color: {DARK_THEME['background']};
                border: none;
            }}
            
            /* Menu Bar */
            QMenuBar {{
                background-color: {DARK_THEME['header_bg']};
                color: {DARK_THEME['foreground']};
                border-bottom: 1px solid {DARK_THEME['border']};
                padding: 4px;
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {DARK_THEME['secondary']};
            }}
            
            QMenu {{
                background-color: {DARK_THEME['card_bg']};
                border: 1px solid {DARK_THEME['border']};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {DARK_THEME['secondary']};
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: 1px solid {DARK_THEME['border']};
                background-color: {DARK_THEME['card_bg']};
                border-radius: 4px;
            }}
            
            QTabBar::tab {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border-bottom: 2px solid transparent;
            }}
            
            QTabBar::tab:selected {{
                background-color: {DARK_THEME['background']};
                border-bottom: 2px solid {DARK_THEME['accent']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {DARK_THEME['header_bg']};
                border-bottom: 2px solid {DARK_THEME['accent_hover']};
            }}
            
            /* Push Buttons */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 {DARK_THEME['button_gradient_top']},
                                          stop:1 {DARK_THEME['button_gradient_bottom']});
                color: {DARK_THEME['foreground']};
                border: 1px solid {DARK_THEME['button_gradient_bottom']};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 {DARK_THEME['accent_hover']},
                                          stop:1 {DARK_THEME['accent']});
            }}
            
            QPushButton:pressed {{
                background: {DARK_THEME['button_gradient_bottom']};
            }}
            
            QPushButton:disabled {{
                background: #666666;
                color: #333333;
                border: 1px solid #555555;
            }}
            
            /* Combo Box */
            QComboBox {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            
            QComboBox:hover {{
                border: 1px solid {DARK_THEME['accent']};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                border: 1px solid {DARK_THEME['border']};
                selection-background-color: {DARK_THEME['secondary']};
            }}
            
            /* Line Edit */
            QLineEdit {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            
            QLineEdit:hover, QLineEdit:focus {{
                border: 1px solid {DARK_THEME['accent']};
            }}
            
            /* Table View */
            QTableView {{
                background-color: {DARK_THEME['card_bg']};
                alternate-background-color: {DARK_THEME['background']};
                border: 1px solid {DARK_THEME['border']};
                gridline-color: {DARK_THEME['border']};
                border-radius: 4px;
            }}
            
            QTableView::item {{
                padding: 4px;
            }}
            
            QTableView::item:selected {{
                background-color: {DARK_THEME['secondary']};
                color: {DARK_THEME['foreground']};
            }}
            
            QHeaderView::section {{
                background-color: {DARK_THEME['header_bg']};
                color: {DARK_THEME['foreground']};
                padding: 6px;
                border: 1px solid {DARK_THEME['border']};
                border-radius: 0px;
                font-weight: bold;
            }}
            
            /* Scroll Bar */
            QScrollBar:vertical {{
                background-color: {DARK_THEME['card_bg']};
                width: 14px;
                margin: 0px;
                border-radius: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {DARK_THEME['border']};
                border-radius: 4px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {DARK_THEME['accent']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {DARK_THEME['card_bg']};
                height: 14px;
                margin: 0px;
                border-radius: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {DARK_THEME['border']};
                border-radius: 4px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {DARK_THEME['accent']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            /* Group Box */
            QGroupBox {{
                border: 1px solid {DARK_THEME['border']};
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                background-color: {DARK_THEME['header_bg']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 3px;
            }}
            
            /* Label styles */
            QLabel {{
                color: {DARK_THEME['foreground']};
            }}
            
            QLabel[title="true"] {{
                font-size: 16px;
                font-weight: bold;
                color: {DARK_THEME['accent']};
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {DARK_THEME['border']};
            }}
            
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            
            /* Status Bar */
            QStatusBar {{
                background-color: {DARK_THEME['header_bg']};
                color: {DARK_THEME['foreground']};
                border-top: 1px solid {DARK_THEME['border']};
            }}
            
            QStatusBar QLabel {{
                padding: 3px;
            }}
            
            /* Frame */
            QFrame[frameShape="4"], QFrame[frameShape="5"] {{
                color: {DARK_THEME['border']};
            }}
        """)

class CustomTableModel(QAbstractTableModel):
    """Custom table model for PySide6 TableView"""
    
    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data if data is not None else []
        self._headers = headers if headers is not None else []
        
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.BackgroundRole:
            # Alternate row colors for better readability
            if index.row() % 2 == 0:
                return QColor(DARK_THEME['card_bg'])
            else:
                return QColor(DARK_THEME['background'])
        elif role == Qt.TextAlignmentRole:
            # Align numbers to the right, text to the left
            value = self._data[index.row()][index.column()]
            if isinstance(value, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        return None
        
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
        
    def columnCount(self, parent=QModelIndex()):
        if self._data:
            return len(self._data[0])
        return len(self._headers)
        
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section < len(self._headers):
            return self._headers[section]
        return None
    
    def setData(self, data, headers):
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
        
    def sort(self, column, order):
        """Sort table by given column number."""
        self.beginResetModel()
        self._data = sorted(self._data, key=lambda x: x[column], reverse=(order == Qt.DescendingOrder))
        self.endResetModel()

class MplCanvas(FigureCanvas):
    """Canvas for matplotlib charts"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """Initialize the canvas with dark theme"""
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor(DARK_THEME['card_bg'])
        
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor(DARK_THEME['card_bg'])
        self.axes.tick_params(colors=DARK_THEME['foreground'])
        self.axes.xaxis.label.set_color(DARK_THEME['foreground'])
        self.axes.yaxis.label.set_color(DARK_THEME['foreground'])
        self.axes.title.set_color(DARK_THEME['accent'])
        
        # Set spines (chart borders) to the border color
        for spine in self.axes.spines.values():
            spine.set_color(DARK_THEME['border'])
        
        # Define gold accent colors for chart elements
        self.chart_colors = [
            DARK_THEME['accent'],        # Gold
            DARK_THEME['secondary'],     # Blue
            '#A6564B',                   # Red
            '#56A64B',                   # Green 
            '#6C567B',                   # Purple
            '#AA8239',                   # Dark gold
            '#4B7AA6',                   # Light blue
            '#A64B98',                   # Pink
            '#4BA657',                   # Teal
            '#FFD700'                    # Bright gold
        ]
        
        super().__init__(self.fig)
        self.setParent(parent)

class DropArea(QWidget):
    """Custom widget for handling file drops"""
    
    fileDropped = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Debug flag for verbose logging
        self.debug = True
        
        # Get access to the main window's config manager
        self.main_window = self.get_main_window()
        
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Add a label and icon
        self.label = QLabel("Please select a CSV File here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setProperty("titleLabel", "true")
        
        self.icon_label = QLabel("📄")
        self.icon_label.setStyleSheet(f"font-size: 48px; color: {DARK_THEME['accent']};")
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Add alternative method text
        self.alt_label = QLabel("or")
        self.alt_label.setAlignment(Qt.AlignCenter)
        
        # Add button for file selection
        self.select_button = QPushButton("Select CSV File")
        self.select_button.clicked.connect(self.open_file_dialog)
        
        # Add to layout
        layout.addWidget(self.label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.alt_label)
        layout.addWidget(self.select_button, 0, Qt.AlignCenter)
        
        self.setLayout(layout)
        self._update_style(False)
    
    def get_main_window(self):
        """Find the main window parent"""
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parent()
        return None
    
    def open_file_dialog(self):
        """Open a file dialog to select a CSV file"""
        if self.main_window and hasattr(self.main_window, 'config_manager'):
            # Get the import directory from config
            start_dir = self.main_window.config_manager.get_last_used_directory()
        else:
            # Fallback to current directory if config manager is not available
            start_dir = ""
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", start_dir, "CSV Files (*.csv)"
        )
        
        if filepath:
            if self.debug:
                print(f"File selected via dialog: {filepath}")
                
            # Update last used directory in config if possible
            if self.main_window and hasattr(self.main_window, 'config_manager'):
                self.main_window.config_manager.set_last_used_directory(str(Path(filepath).parent))
                
            self.fileDropped.emit(filepath)
    
    def _update_style(self, highlight=False):
        """Update the border style of the drop area"""
        border_color = DARK_THEME['accent'] if highlight else DARK_THEME['border']
        bg_color = DARK_THEME['card_bg'] if not highlight else DARK_THEME['background']
        self.setStyleSheet(f"""
            QWidget {{
                border: 2px dashed {border_color};
                border-radius: 8px;
                background-color: {bg_color};
                padding: 16px;
            }}
            
            QLabel {{
                border: none;
                background-color: transparent;
                padding: 0px;
            }}
            
            QLabel[titleLabel="true"] {{
                color: {DARK_THEME['accent']};
                font-size: 16px;
                font-weight: bold;
            }}
        """)

    def mousePressEvent(self, event):
        """Handle mouse press events to provide button-like interaction"""
        if event.button() == Qt.LeftButton:
            self.open_file_dialog()
            
class ImportArea(QWidget):
    """Widget for importing CSV files via file selection"""
    
    fileSelected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Debug flag for verbose logging
        self.debug = True
        
        # Get access to the main window's config manager
        self.main_window = self.get_main_window()
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Import CSV File")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setProperty("titleLabel", "true")
        
        # Create and add document icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "document_icon.png")
        
        # If the icon file exists, use it, otherwise create a text label
        if os.path.exists(icon_path):
            self.icon_label = QLabel()
            self.icon_label.setPixmap(QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setProperty("iconLabel", "true")
        else:
            # Create a gold-colored document icon as text
            self.icon_label = QLabel("📄")
            self.icon_label.setStyleSheet(f"font-size: 48px; color: {DARK_THEME['accent']};")
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setProperty("iconLabel", "true")
        
        # Add instructions text
        self.instruction_label = QLabel("Click here or use File > Import CSV to load your data")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setProperty("instructionLabel", "true")
        
        # Add file select button with gold gradient
        self.select_button = QPushButton("Select CSV File")
        self.select_button.setMinimumWidth(150)
        self.select_button.clicked.connect(self.open_file_dialog)
        
        # Create layout
        layout.addWidget(self.label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.instruction_label)
        layout.addSpacing(10)
        layout.addWidget(self.select_button, 0, Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.setLayout(layout)
        self._update_style()
        
        # Make the widget clickable for file selection
        self.setCursor(Qt.PointingHandCursor)
    
    def get_main_window(self):
        """Find the main window parent"""
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parent()
        return None

    def open_file_dialog(self):
        """Open file dialog to select a CSV file"""
        if self.main_window and hasattr(self.main_window, 'config_manager'):
            # Get the import directory from config
            start_dir = self.main_window.config_manager.get_last_used_directory()
        else:
            # Fallback to current directory if config manager is not available
            start_dir = ""
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", start_dir, "CSV Files (*.csv)"
        )
        
        if filepath:
            if self.debug:
                print(f"File selected via dialog: {filepath}")
                
            # Update last used directory in config if possible
            if self.main_window and hasattr(self.main_window, 'config_manager'):
                self.main_window.config_manager.set_last_used_directory(str(Path(filepath).parent))
                
            self.fileSelected.emit(filepath)
    
    def _update_style(self):
        """Update the styling of the import area"""
        self.setStyleSheet(f"""
            QWidget {{
                border: 2px dashed {DARK_THEME['accent']};
                border-radius: 8px;
                background-color: {DARK_THEME['card_bg']};
                padding: 16px;
            }}
            
            QLabel[iconLabel="true"] {{
                border: none;
                background-color: transparent;
                padding: 0px;
            }}
            
            QLabel[titleLabel="true"] {{
                border: none;
                background-color: transparent;
                color: {DARK_THEME['accent']};
                font-size: 16px;
                font-weight: bold;
                padding: 0px;
            }}
            
            QLabel[instructionLabel="true"] {{
                border: none;
                background-color: transparent;
                padding: 0px;
                color: {DARK_THEME['foreground']};
            }}
        """)

    def mousePressEvent(self, event):
        """Handle mouse press events to provide button-like interaction"""
        if event.button() == Qt.LeftButton:
            self.open_file_dialog()

class DataProcessor:
    """Class to handle data processing logic"""
    
    # Debug flag
    debug = True
    
    @staticmethod
    def load_csv(filepath):
        """
        Load CSV data from file and return as pandas DataFrame.
        
        Attempts different encodings if the default UTF-8 fails.
        Provides detailed error logging for troubleshooting.
        
        Args:
            filepath: Path to the CSV file
            
        Returns:
            pandas.DataFrame: The loaded CSV data
            
        Raises:
            ValueError: If the file can't be loaded for any reason
        """
        print("\n=== DataProcessor.load_csv ===")
        print(f"Processing filepath: {filepath}")
        print(f"Type of filepath: {type(filepath)}")
        
        if DataProcessor.debug:
            print(f"DataProcessor.load_csv: Processing {filepath}")
            print(f"File exists check: {os.path.exists(filepath)}")
            
        if not os.path.exists(filepath):
            error_msg = f"File does not exist: {filepath}"
            print(error_msg)
            raise ValueError(error_msg)
            
        if not os.path.isfile(filepath):
            error_msg = f"Path is not a file: {filepath}"
            print(error_msg)
            raise ValueError(error_msg)
            
        # Check file size
        try:
            file_size = os.path.getsize(filepath)
            if DataProcessor.debug:
                print(f"File size: {file_size} bytes")
                
            if file_size == 0:
                error_msg = "File is empty (0 bytes)"
                print(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            print(f"Error checking file size: {str(e)}")
            # Continue anyway - might still be loadable
        
        # Try to read the first few bytes to check if file is accessible
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(32)
                if DataProcessor.debug:
                    print(f"First bytes: {first_bytes}")
                    print(f"First bytes (hex): {first_bytes.hex()}")
                    
                # Check if the first bytes look like a CSV file
                # CSV files typically start with ASCII characters like letters, numbers, or common punctuation
                if first_bytes and all(b < 127 for b in first_bytes):
                    if DataProcessor.debug:
                        print("First bytes look like valid ASCII/text data")
                else:
                    if DataProcessor.debug:
                        print("Warning: First bytes don't look like standard text/CSV data")
                    # Continue anyway - might still be decodable with the right encoding
                    
                # Check for German umlauts in the first bytes
                umlaut_patterns = [
                    b'\xe4',  # ä in latin1/cp1252
                    b'\xf6',  # ö in latin1/cp1252
                    b'\xfc',  # ü in latin1/cp1252
                    b'\xc4',  # Ä in latin1/cp1252
                    b'\xd6',  # Ö in latin1/cp1252
                    b'\xdc',  # Ü in latin1/cp1252
                    b'\xdf'   # ß in latin1/cp1252
                ]
                
                has_potential_umlauts = any(pattern in first_bytes for pattern in umlaut_patterns)
                if has_potential_umlauts:
                    print("Detected potential German umlauts in the first bytes")
                
                # Also read more content to check for umlauts that might not be in the first 32 bytes
                f.seek(0)
                more_content = f.read(4096)  # Read more content to increase chances of finding umlauts
                has_potential_umlauts_extended = any(pattern in more_content for pattern in umlaut_patterns)
                if has_potential_umlauts_extended and not has_potential_umlauts:
                    print("Detected potential German umlauts in extended content")
                    has_potential_umlauts = True
        except Exception as e:
            error_msg = f"Failed to open file for reading: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
        
        # Get config manager if available
        config_manager = None
        try:
            # Try to find a MainWindow instance to get the config manager
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    config_manager = widget.config_manager
                    break
        except Exception as e:
            print(f"Error getting config manager: {str(e)}")
        
        # List of encodings to try, in order of preference
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252', 'utf-8-sig']
        
        # If we have a config manager, use the encodings from the config
        if config_manager:
            try:
                # Get default encoding
                default_encoding = config_manager.get('Data', 'default_encoding', 'utf-8')
                
                # Get alternative encodings
                alt_encodings_str = config_manager.get('Data', 'alternative_encodings', 
                                                      'latin1,iso-8859-1,cp1252,windows-1252,utf-8-sig')
                alt_encodings = [enc.strip() for enc in alt_encodings_str.split(',')]
                
                # Get German encodings if we detected umlauts
                if has_potential_umlauts:
                    german_encodings_str = config_manager.get('Data', 'german_encodings', 
                                                             'latin1,cp1252,iso-8859-1,windows-1252')
                    german_encodings = [enc.strip() for enc in german_encodings_str.split(',')]
                    
                    # Prioritize German encodings if we detected umlauts
                    encodings_to_try = [default_encoding] + german_encodings + alt_encodings
                else:
                    encodings_to_try = [default_encoding] + alt_encodings
                
                # Remove duplicates while preserving order
                seen = set()
                encodings_to_try = [enc for enc in encodings_to_try if not (enc in seen or seen.add(enc))]
                
                print(f"Using encodings from config: {encodings_to_try}")
            except Exception as e:
                print(f"Error getting encodings from config: {str(e)}")
                # Fall back to default encodings
        
        print(f"Trying encodings in sequence: {encodings_to_try}")
        
        # Try pandas directly first with each encoding
        last_error = None
        for encoding in encodings_to_try:
            try:
                if DataProcessor.debug:
                    print(f"Trying to load with encoding: {encoding}")
                
                # Try to read with pandas
                df = pd.read_csv(filepath, encoding=encoding)
                
                if DataProcessor.debug:
                    print(f"Successfully loaded with encoding: {encoding}")
                    print(f"DataFrame shape: {df.shape}")
                    print(f"Columns: {df.columns.tolist()}")
                    print(f"First row: {df.iloc[0].tolist() if not df.empty else 'Empty DataFrame'}")
                    
                    # Check for German characters in the data
                    sample_data = df.head(5).to_string()
                    print(f"Sample data (first 5 rows):\n{sample_data}")
                    
                    # Check for both properly formatted umlauts and common garbled representations
                    has_proper_umlauts = any(char in sample_data for char in 'äöüÄÖÜß')
                    
                    # Check for garbled umlaut representations (common when encoding is mismatched)
                    garbled_umlaut_patterns = ['Ã¤', 'Ã¶', 'Ã¼', 'Ã„', 'Ã–', 'Ãœ', 'ÃŸ',  # UTF-8 misinterpreted as Latin-1
                                              'ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß',           # Correct representations
                                              'a\u0308', 'o\u0308', 'u\u0308',             # Decomposed forms
                                              'A\u0308', 'O\u0308', 'U\u0308',             # Decomposed uppercase
                                              'FeldjÃ¤ger', 'Feldjäger',                  # Common specific cases
                                              'ÃƒÂ¤', 'ÃƒÂ¶', 'ÃƒÂ¼']                     # Double-encoding cases
                    
                    has_garbled_umlauts = any(pattern in sample_data for pattern in garbled_umlaut_patterns)
                    
                    if has_proper_umlauts:
                        print(f"Data contains properly formatted German umlauts")
                    elif has_garbled_umlauts:
                        print(f"Data contains garbled German umlauts (encoding mismatch detected)")
                        
                        # If we have garbled umlauts, try to fix them when the encoding is wrong
                        if 'FeldjÃ¤ger' in sample_data:
                            print("Found misencoded 'FeldjÃ¤ger' - this should be 'Feldjäger'")
                            
                            # If it's in the PLAYER column, we could try to fix it
                            if 'PLAYER' in df.columns and df['PLAYER'].str.contains('FeldjÃ¤ger').any():
                                print("Attempting to fix encoding for the PLAYER column")
                                # This is a specific fix for this case - adjust as needed
                                df['PLAYER'] = df['PLAYER'].str.replace('FeldjÃ¤ger', 'Feldjäger')
                    
                    print(f"Data contains German umlauts (properly formatted or garbled): {has_proper_umlauts or has_garbled_umlauts}")
                    
                    # Check if required columns are present
                    required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        error_msg = f"Missing required columns: {missing_columns}. CSV file must contain all of these columns: {required_columns}"
                        print(error_msg)
                        raise ValueError(error_msg)
                    
                    # Keep only the required columns, drop everything else
                    extra_columns = [col for col in df.columns if col not in required_columns]
                    if extra_columns:
                        print(f"Dropping extra columns: {extra_columns}")
                        df = df[required_columns]
                    
                    print("=== CSV loaded successfully ===\n")
                    return df
                
            except UnicodeDecodeError as e:
                # Log the specific encoding error and try the next one
                if DataProcessor.debug:
                    print(f"UnicodeDecodeError with {encoding}: {str(e)}")
                last_error = e
                continue
                
            except pd.errors.EmptyDataError as e:
                # File is empty or contains no data
                error_msg = f"CSV file is empty or contains no parsable data: {str(e)}"
                print(error_msg)
                raise ValueError(error_msg)
                
            except pd.errors.ParserError as e:
                # File doesn't seem to be a valid CSV
                error_msg = f"Not a valid CSV file - parser error: {str(e)}"
                print(error_msg)
                
                # Try with a different separator as a fallback
                try:
                    if DataProcessor.debug:
                        print(f"Trying with different separator (semicolon) for {encoding}")
                    df = pd.read_csv(filepath, encoding=encoding, sep=';')
                    if DataProcessor.debug:
                        print(f"Success with semicolon separator using {encoding}")
                    
                    # Check for German umlauts again with the new separator
                    sample_data = df.head(5).to_string()
                    
                    # Check for both proper and garbled umlauts
                    has_proper_umlauts = any(char in sample_data for char in 'äöüÄÖÜß')
                    garbled_umlaut_patterns = ['Ã¤', 'Ã¶', 'Ã¼', 'Ã„', 'Ã–', 'Ãœ', 'ÃŸ', 'FeldjÃ¤ger']
                    has_garbled_umlauts = any(pattern in sample_data for pattern in garbled_umlaut_patterns)
                    
                    print(f"Data with semicolon separator contains German umlauts: {has_proper_umlauts or has_garbled_umlauts}")
                    
                    # Check if required columns are present
                    required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        error_msg = f"Missing required columns: {missing_columns}. CSV file must contain all of these columns: {required_columns}"
                        print(error_msg)
                        raise ValueError(error_msg)
                    
                    # Keep only the required columns, drop everything else
                    extra_columns = [col for col in df.columns if col not in required_columns]
                    if extra_columns:
                        print(f"Dropping extra columns: {extra_columns}")
                        df = df[required_columns]
                    
                    print("=== CSV loaded successfully with semicolon separator ===\n")
                    return df
                except Exception as sep_e:
                    if DataProcessor.debug:
                        print(f"Alternative separator failed: {str(sep_e)}")
                    # Continue to the next encoding
                    last_error = e
                    continue
                
            except Exception as e:
                # For other exceptions, log and try the next encoding
                error_msg = f"Error loading CSV file with {encoding}: {str(e)}"
                print(error_msg)
                last_error = e
                continue
                
        # If we've tried all encodings and none worked, try a more manual approach
        try:
            if DataProcessor.debug:
                print("Trying manual file reading approach...")
            
            # Read the file as bytes and try to detect the encoding
            with open(filepath, 'rb') as f:
                content = f.read()
                
            print(f"File content size: {len(content)} bytes")
            print(f"First 100 bytes (hex): {content[:100].hex()}")
            
            # Check for BOM markers that might indicate encoding
            if content.startswith(b'\xef\xbb\xbf'):
                print("Detected UTF-8 BOM marker")
                # Try UTF-8 with BOM
                try:
                    text = content.decode('utf-8-sig')
                    print("Successfully decoded with utf-8-sig (UTF-8 with BOM)")
                    import io
                    df = pd.read_csv(io.StringIO(text))
                    
                    # Process as before
                    if 'CLAN' in df.columns:
                        df = df.drop(columns=['CLAN'])
                        print("Removed CLAN column")
                    
                    # Check if required columns are present
                    required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        error_msg = f"Missing required columns: {missing_columns}. CSV file must contain all of these columns: {required_columns}"
                        print(error_msg)
                        raise ValueError(error_msg)
                    
                    # Keep only the required columns, drop everything else
                    extra_columns = [col for col in df.columns if col not in required_columns]
                    if extra_columns:
                        print(f"Dropping extra columns: {extra_columns}")
                        df = df[required_columns]
                    
                    print("=== CSV loaded successfully via UTF-8 with BOM ===\n")
                    return df
                except Exception as e:
                    print(f"Failed to decode with utf-8-sig: {str(e)}")
            
            # Try to detect German umlauts in the content
            german_encodings = ['latin1', 'cp1252', 'iso-8859-1', 'windows-1252']
            
            # Look for byte patterns that might be German umlauts
            umlaut_patterns = [
                b'\xe4',  # ä in latin1/cp1252
                b'\xf6',  # ö in latin1/cp1252
                b'\xfc',  # ü in latin1/cp1252
                b'\xc4',  # Ä in latin1/cp1252
                b'\xd6',  # Ö in latin1/cp1252
                b'\xdc',  # Ü in latin1/cp1252
                b'\xdf'   # ß in latin1/cp1252
            ]
            
            has_potential_umlauts = any(pattern in content for pattern in umlaut_patterns)
            if has_potential_umlauts:
                print("Detected potential German umlauts in the file")
                # Try German encodings first
                for encoding in german_encodings:
                    try:
                        text = content.decode(encoding)
                        print(f"Successfully decoded content with {encoding} (German encoding)")
                        
                        # Check for both properly formatted umlauts and common garbled representations
                        has_proper_umlauts = any(char in text for char in 'äöüÄÖÜß')
                        
                        # Check for specific German name patterns that should contain umlauts
                        has_german_names = 'Feldjager' in text or 'Feldjaeger' in text or 'Jager' in text
                        
                        if has_proper_umlauts:
                            print(f"Decoded text contains properly formatted German umlauts")
                        
                        if has_german_names:
                            print(f"Detected German names that should contain umlauts but might be missing them")
                        
                        print(f"Decoded text contains German umlauts: {has_proper_umlauts}")
                        
                        # Also look for specific patterns like "FeldjÃ¤ger" that indicate encoding issues
                        garbled_patterns = ['FeldjÃ¤ger', 'JÃ¤ger', 'Ã¤', 'Ã¶', 'Ã¼', 'Ã„', 'Ã–', 'Ãœ', 'ÃŸ']
                        has_garbled_umlauts = any(pattern in text for pattern in garbled_patterns)
                        
                        if has_garbled_umlauts:
                            print(f"Decoded text contains garbled umlauts, indicating possible encoding issues")
                            
                            # Try to fix specific garbled patterns
                            text = text.replace('FeldjÃ¤ger', 'Feldjäger')
                            text = text.replace('JÃ¤ger', 'Jäger')
                            print("Attempted to fix specific garbled umlaut patterns")
                        
                        import io
                        df = pd.read_csv(io.StringIO(text))
                        
                        # Check if we need to fix the dataframe directly
                        if 'PLAYER' in df.columns:
                            # Check for misencoded player names
                            sample_players = ', '.join(df['PLAYER'].head(10).tolist())
                            print(f"Sample player names: {sample_players}")
                            
                            # If we see garbled umlauts in player names, fix them
                            if any(pattern in sample_players for pattern in garbled_patterns):
                                print("Fixing garbled player names in the DataFrame")
                                df['PLAYER'] = df['PLAYER'].str.replace('FeldjÃ¤ger', 'Feldjäger')
                                df['PLAYER'] = df['PLAYER'].str.replace('JÃ¤ger', 'Jäger')
                        
                        # Process as before
                        if 'CLAN' in df.columns:
                            df = df.drop(columns=['CLAN'])
                            print("Removed CLAN column")
                            
                        # Check if required columns are present
                        required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        
                        if missing_columns:
                            error_msg = f"Missing required columns: {missing_columns}. CSV file must contain all of these columns: {required_columns}"
                            print(error_msg)
                            raise ValueError(error_msg)
                        
                        # Keep only the required columns, drop everything else
                        extra_columns = [col for col in df.columns if col not in required_columns]
                        if extra_columns:
                            print(f"Dropping extra columns: {extra_columns}")
                            df = df[required_columns]
                        
                        print("=== CSV loaded successfully via manual decoding ===\n")
                        return df
                    except Exception as e:
                        print(f"Failed to decode with {encoding}: {str(e)}")
                
            # Try each encoding to decode the content
            for encoding in encodings_to_try:
                try:
                    text = content.decode(encoding)
                    if DataProcessor.debug:
                        print(f"Successfully decoded content with {encoding}")
                        print(f"First 100 characters: {text[:100]}")
                    
                    # Check for German characters and try to fix encoding issues
                    contains_umlauts = any(char in text for char in 'äöüÄÖÜß')
                    
                    if contains_umlauts:
                        print(f"Decoded text with {encoding} contains proper umlauts")
                    else:
                        # Look for garbled characters that indicate encoding issues
                        garbled_patterns = ['FeldjÃ¤ger', 'JÃ¤ger', 'Ã¤', 'Ã¶', 'Ã¼', 'Ã„', 'Ã–', 'Ãœ', 'ÃŸ']
                        has_garbled_umlauts = any(pattern in text for pattern in garbled_patterns)
                        
                        if has_garbled_umlauts:
                            print(f"Decoded text contains garbled umlauts with {encoding}")
                            # Try to fix common garbled patterns
                            text = text.replace('FeldjÃ¤ger', 'Feldjäger')
                            text = text.replace('JÃ¤ger', 'Jäger')
                    
                    # Try to convert text to CSV using StringIO
                    import io
                    df = pd.read_csv(io.StringIO(text))
                    
                    if DataProcessor.debug:
                        print(f"Successfully parsed CSV from decoded text")
                        # Display sample data to check for encoding issues
                        sample_data = df.head(5).to_string()
                        print(f"Sample data from decoded text:\n{sample_data}")
                    
                    # Check and fix player names if needed
                    if 'PLAYER' in df.columns:
                        # Check for garbled names
                        if df['PLAYER'].astype(str).str.contains('FeldjÃ¤ger').any() or df['PLAYER'].astype(str).str.contains('JÃ¤ger').any():
                            print("Fixing garbled player names in the DataFrame")
                            df['PLAYER'] = df['PLAYER'].str.replace('FeldjÃ¤ger', 'Feldjäger')
                            df['PLAYER'] = df['PLAYER'].str.replace('JÃ¤ger', 'Jäger')
                            
                            # Check if fixed
                            contains_fixed_umlauts = df['PLAYER'].astype(str).str.contains('Feldjäger').any()
                            print(f"DataFrame now contains properly formatted player names: {contains_fixed_umlauts}")
                    
                    # Process as before
                    if 'CLAN' in df.columns:
                        df = df.drop(columns=['CLAN'])
                        print("Removed CLAN column")
                        
                    # Check if required columns are present
                    required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        error_msg = f"Missing required columns: {missing_columns}. CSV file must contain all of these columns: {required_columns}"
                        print(error_msg)
                        raise ValueError(error_msg)
                    
                    # Keep only the required columns, drop everything else
                    extra_columns = [col for col in df.columns if col not in required_columns]
                    if extra_columns:
                        print(f"Dropping extra columns: {extra_columns}")
                        df = df[required_columns]
                    
                except UnicodeDecodeError:
                    # Try the next encoding
                    if DataProcessor.debug:
                        print(f"Failed to decode content with {encoding}")
                    continue
                except Exception as e:
                    # Other errors (like CSV parsing)
                    if DataProcessor.debug:
                        print(f"Error parsing CSV with {encoding}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Manual file reading approach failed: {str(e)}")
            
        # If we get here, we've tried everything and failed
        if last_error:
            error_msg = f"Failed to load CSV file after trying multiple encodings. Last error: {str(last_error)}"
        else:
            error_msg = "Failed to load CSV file after trying multiple approaches."
            
        print(f"CSV LOADING FAILED: {error_msg}")
        print("=== End of DataProcessor.load_csv (with errors) ===\n")
        raise ValueError(error_msg)
    
    @staticmethod
    def analyze_data(df):
        """Process data according to requirements and return processed DataFrames"""
        # Calculate total score per player (main goal)
        player_totals = df.groupby('PLAYER')['SCORE'].sum().reset_index()
        player_totals = player_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by chest type
        chest_totals = df.groupby('CHEST')['SCORE'].sum().reset_index()
        chest_totals = chest_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by source
        source_totals = df.groupby('SOURCE')['SCORE'].sum().reset_index()
        source_totals = source_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by date
        date_totals = df.groupby('DATE')['SCORE'].sum().reset_index()
        date_totals = date_totals.sort_values('DATE')
        
        # Calculate average scores
        player_avg = df.groupby('PLAYER')['SCORE'].mean().reset_index()
        player_avg = player_avg.sort_values('SCORE', ascending=False)
        player_avg['SCORE'] = player_avg['SCORE'].round(2)
        
        # Calculate number of chests per player
        player_counts = df.groupby('PLAYER').size().reset_index(name='COUNT')
        player_counts = player_counts.sort_values('COUNT', ascending=False)
        
        # Most frequent chest types per player
        player_chest_freq = df.groupby(['PLAYER', 'CHEST']).size().reset_index(name='COUNT')
        
        return {
            'player_totals': player_totals,
            'chest_totals': chest_totals,
            'source_totals': source_totals,
            'date_totals': date_totals,
            'player_avg': player_avg,
            'player_counts': player_counts,
            'player_chest_freq': player_chest_freq,
            'raw_data': df
        }

class MainWindow(QMainWindow):
    """Main window for the Total Battle Analyzer application"""
    
    def __init__(self):
        super().__init__()
        
        # Enable drop acceptance at the MainWindow level
        self.setAcceptDrops(True)
        
        # Debug flag for verbose logging
        self.debug = True
        
        # Initialize config manager
        self.config_manager = ConfigManager()
        
        self.raw_data = None
        self.raw_data_model = None
        self.raw_data_proxy_model = None
        self.current_filepath = None
        
        self.setup_ui()
        # Menu is now setup in setup_ui method
        
        # Set window size from config
        width = self.config_manager.get_int('General', 'window_width', 1200)
        height = self.config_manager.get_int('General', 'window_height', 800)
        self.resize(width, height)
        self.setWindowTitle("Total Battle Analyzer")
        
        # Connect signals and slots
        if hasattr(self, 'drop_area'):
            self.drop_area.fileDropped.connect(self.load_csv_file)
        
        self.statusBar().showMessage("Ready", 3000)
    
    def closeEvent(self, event):
        """Handle window close event to save settings"""
        # Save window size to config
        self.config_manager.set('General', 'window_width', self.width())
        self.config_manager.set('General', 'window_height', self.height())
        
        # Accept the event and close the window
        event.accept()
    
    def setup_ui(self):
        """Set up the application's main user interface"""
        # Set window properties
        self.setWindowTitle("Total Battle Analyzer")
        self.setMinimumSize(900, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create application title with gold styling
        title_layout = QHBoxLayout()
        title_label = QLabel("Total Battle Analyzer")
        title_label.setProperty("title", "true")
        title_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {DARK_THEME['accent']};
            padding: 10px;
            border-bottom: 2px solid {DARK_THEME['accent']};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        main_layout.addLayout(title_layout)
        
        # Create tab widget and add to layout
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        
        # Create tabs
        self.setup_import_tab()
        self.setup_raw_data_tab()
        self.setup_analysis_tab()
        self.setup_charts_tab()
        
        # Add tabs to widget
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Set up the menu bar
        self.setup_menu()
    
    def setup_menu(self):
        """Set up the application menu"""
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Add Import action
        import_action = file_menu.addAction("&Import CSV File...")
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self.open_file_dialog)
        
        # Add Export action
        export_action = file_menu.addAction("&Export Results...")
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.export_current_analysis)
        
        # Add Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Create Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Add About action
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about_dialog)
    
    def open_file_dialog(self):
        """Open a file dialog to select a CSV file"""
        # Get the last used directory from config
        start_dir = self.config_manager.get_last_used_directory()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", start_dir, "CSV Files (*.csv)"
        )
        
        if filepath:
            # Save the directory for next time
            self.config_manager.set_last_used_directory(str(Path(filepath).parent))
            self.load_csv_file(filepath)
    
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(
            self, 
            "About Total Battle Analyzer",
            """
            <h1>Total Battle Analyzer</h1>
            <p>A tool for analyzing data from the Total Battle game.</p>
            <p>Version 1.0</p>
            """
        )
    
    def setup_import_tab(self):
        """Setup the import tab UI"""
        import_tab = QWidget()
        layout = QVBoxLayout()
        
        # Create import instructions
        info_group = QGroupBox("Import Instructions")
        info_layout = QVBoxLayout()
        
        instructions = QLabel(
            "To import data from a CSV file:\n"
            "1. Click the 'Select CSV File' button below\n"
            "2. Or use File → Import CSV... from the menu (Ctrl+O)\n\n"
            "The CSV file MUST contain ALL of the following columns:\n"
            "DATE, PLAYER, SOURCE, CHEST, SCORE\n\n"
            "Files missing any of these columns will be rejected.\n"
            "Any additional columns will be automatically removed."
        )
        instructions.setWordWrap(True)
        info_layout.addWidget(instructions)
        
        info_group.setLayout(info_layout)
        
        # Create import area for file selection
        self.import_area = DropArea()
        self.import_area.fileDropped.connect(self.load_csv_file)
        
        # Add widgets to layout
        layout.addWidget(info_group)
        layout.addWidget(self.import_area)
        
        # Set layout for import tab
        import_tab.setLayout(layout)
        
        # Add to tabs
        self.tabs.addTab(import_tab, "Import")
    
    def test_drag_drop_system(self):
        """Diagnostic function to test if drag and drop handlers are working"""
        print("\n===== TESTING DRAG AND DROP SYSTEM =====")
        print("This will simulate a drop event with a test file path")
        
        # Create a test file
        test_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_file.csv")
        print(f"Test file path: {test_file_path}")
        
        try:
            # Create a simple CSV file for testing
            with open(test_file_path, 'w', newline='') as f:
                f.write("DATE,PLAYER,SOURCE,CHEST,SCORE\n")
                f.write("2024-03-16,TestPlayer,Test Source,Test Chest,100\n")
        except Exception as e:
            print(f"Error creating test file: {str(e)}")
            return
        
        # Direct load test
        print("\n=== BYPASSING DRAG AND DROP WITH DIRECT LOAD ===")
        print(f"Directly calling load_csv_file with path: {test_file_path}")
        self.load_csv_file(test_file_path)
        print("=== END OF DIRECT LOAD TEST ===\n")
        
        # Cleanup the test file
        try:
            os.remove(test_file_path)
        except:
            pass
            
        print("\nIf the direct load worked but drag and drop doesn't,")
        print("this confirms a system-level issue with Qt drag and drop.")
        print("===== END OF DRAG AND DROP TEST =====\n")
    
    def setup_raw_data_tab(self):
        """Setup the raw data tab UI"""
        raw_data_tab = QWidget()
        layout = QVBoxLayout()
        
        # Create filter section
        filter_group = QGroupBox("Filter Data")
        filter_layout = QHBoxLayout()
        
        # Column selector
        self.column_selector = QComboBox()
        
        # Value selector
        self.value_selector = QComboBox()
        
        # Apply filter button
        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.filter_raw_data)
        
        # Clear filter button
        self.clear_filter_button = QPushButton("Clear Filter")
        self.clear_filter_button.clicked.connect(lambda: self.raw_data_proxy_model.setFilterFixedString("") if hasattr(self, 'raw_data_proxy_model') else None)
        
        # Add widgets to filter layout
        filter_layout.addWidget(QLabel("Column:"))
        filter_layout.addWidget(self.column_selector)
        filter_layout.addWidget(QLabel("Value:"))
        filter_layout.addWidget(self.value_selector)
        filter_layout.addWidget(self.apply_filter_button)
        filter_layout.addWidget(self.clear_filter_button)
        
        filter_group.setLayout(filter_layout)
        
        # Create table view for raw data
        self.raw_data_table = QTableView()
        self.raw_data_table.setSortingEnabled(True)
        self.raw_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.raw_data_table.horizontalHeader().setMinimumSectionSize(80)
        self.raw_data_table.setAlternatingRowColors(True)
        
        # Connect column selection to update value options
        self.column_selector.currentIndexChanged.connect(self.update_filter_options)
        
        # Add widgets to main layout
        layout.addWidget(filter_group)
        layout.addWidget(self.raw_data_table)
        
        # Set layout for raw data tab
        raw_data_tab.setLayout(layout)
        
        # Add to tabs
        self.tabs.addTab(raw_data_tab, "Raw Data")
    
    def setup_analysis_tab(self):
        """Setup the analysis tab UI"""
        analysis_tab = QWidget()
        layout = QVBoxLayout()
        
        # Create analysis controls
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout()
        
        # Analysis selector
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems([
            "Player Total Scores", 
            "Scores by Chest Type", 
            "Scores by Source",
            "Scores by Date",
            "Player Average Scores",
            "Chest Count by Player"
        ])
        self.analysis_selector.currentIndexChanged.connect(self.update_analysis_view)
        
        # Add widgets to controls layout
        controls_layout.addWidget(QLabel("View:"))
        controls_layout.addWidget(self.analysis_selector)
        controls_layout.addStretch()
        
        controls_group.setLayout(controls_layout)
        
        # Create analysis view
        self.analysis_view = QTableView()
        self.analysis_view.setSortingEnabled(True)
        self.analysis_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.analysis_view.horizontalHeader().setMinimumSectionSize(100)
        self.analysis_view.setAlternatingRowColors(True)
        
        # Create export button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_current_analysis)
        
        # Add widgets to main layout
        layout.addWidget(controls_group)
        layout.addWidget(self.analysis_view)
        layout.addWidget(self.export_button)
        
        # Set layout for analysis tab
        analysis_tab.setLayout(layout)
        
        # Add to tabs
        self.tabs.addTab(analysis_tab, "Analysis")
    
    def setup_charts_tab(self):
        """Setup the charts tab UI"""
        charts_tab = QWidget()
        layout = QVBoxLayout()
        
        # Create chart controls
        controls_group = QGroupBox("Chart Controls")
        controls_layout = QHBoxLayout()
        
        # Chart type selector
        self.chart_type_selector = QComboBox()
        self.chart_type_selector.addItems(["Bar Chart", "Pie Chart", "Line Chart"])
        
        # Chart data selector - use actual column names that match the DataFrame
        self.chart_data_selector = QComboBox()
        self.chart_data_selector.addItems(["PLAYER", "SOURCE", "CHEST"])
        
        # Update chart button
        self.update_chart_button = QPushButton("Update Chart")
        self.update_chart_button.clicked.connect(self.update_chart)
        
        # Add widgets to controls layout
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type_selector)
        controls_layout.addWidget(QLabel("Data:"))
        controls_layout.addWidget(self.chart_data_selector)
        controls_layout.addWidget(self.update_chart_button)
        
        controls_group.setLayout(controls_layout)
        
        # Create matplotlib canvas
        self.mpl_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        
        # Add widgets to main layout
        layout.addWidget(controls_group)
        layout.addWidget(self.mpl_canvas)
        
        # Set layout for charts tab
        charts_tab.setLayout(layout)
        
        # Add to tabs
        self.tabs.addTab(charts_tab, "Charts")
    
    def load_csv_file(self, filepath):
        """
        Load CSV file and display data.
        
        This function handles various filepath formats and provides detailed error info.
        
        Args:
            filepath: The path to the CSV file to load
        """
        print("\n========== Starting load_csv_file ==========")
        print(f"Received filepath: {filepath}")
        print(f"Type of filepath: {type(filepath)}")
        
        try:
            # Handle various filepath formats
            original_filepath = filepath
            
            if self.debug:
                print(f"Starting to load file: {filepath}")
                print(f"Original path type: {type(filepath)}")
            
            # Try to normalize the path in the most robust way possible
            try:
                # Convert to string if needed
                if not isinstance(filepath, (str, Path)):
                    filepath = str(filepath)
                    print(f"Converted to string: {filepath}")
                    
                # Convert to Path object for robustness
                path_obj = Path(filepath)
                
                # Resolve and convert to string in platform-friendly way
                filepath = str(path_obj.resolve())
                
                if self.debug:
                    print(f"Normalized path: {filepath}")
                    print(f"Path exists check: {os.path.exists(filepath)}")
            except Exception as e:
                print(f"Path normalization warning (continuing with original path): {str(e)}")
                filepath = original_filepath
            
            if self.debug:
                print(f"Loading CSV file: {filepath}")
                if os.path.exists(filepath):
                    print(f"File exists: Yes")
                    print(f"File readable: {os.access(filepath, os.R_OK)}")
                    print(f"File size: {os.path.getsize(filepath)}")
                    
                    # Try to read the first few bytes
                    try:
                        with open(filepath, 'rb') as f:
                            first_bytes = f.read(32)
                            print(f"First bytes: {first_bytes}")
                    except Exception as file_e:
                        print(f"Warning: Could not read file bytes: {str(file_e)}")
                else:
                    print(f"File does not exist at: {filepath}")
                    # Try to check the directory
                    parent_dir = os.path.dirname(filepath)
                    if parent_dir and os.path.exists(parent_dir):
                        print(f"Parent directory exists: {parent_dir}")
                        print(f"Directory contents: {os.listdir(parent_dir)}")
            
            self.statusBar().showMessage(f"Loading {filepath}...", 2000)
            
            try:
                # Load CSV data with improved error handling
                print(f"Calling DataProcessor.load_csv with filepath: {filepath}")
                self.raw_data = DataProcessor.load_csv(filepath)
                
                if self.raw_data is None or self.raw_data.empty:
                    QMessageBox.warning(self, "Warning", "The loaded CSV file contains no data.")
                    self.statusBar().showMessage("CSV file loaded but contains no data", 5000)
                    print("CSV file loaded but contains no data")
                    return
                    
                if self.debug:
                    print(f"Successfully loaded CSV with {len(self.raw_data)} rows and {len(self.raw_data.columns)} columns")
                    print(f"Columns: {self.raw_data.columns.tolist()}")
                    print(f"First row: {self.raw_data.iloc[0].tolist() if not self.raw_data.empty else 'N/A'}")
                
                # Update UI with data
                print("Updating UI with loaded data")
                self.update_raw_data_view()
                self.analyze_data()
                
                # Switch to Raw Data tab
                self.tabs.setCurrentIndex(1)
                
                self.statusBar().showMessage(f"Loaded {len(self.raw_data)} records from {filepath}", 5000)
                
                # Store the file path
                self.current_filepath = filepath
                
                # Update file info label if it exists
                if hasattr(self, 'file_info_label'):
                    self.file_info_label.setText(f"Loaded: {os.path.basename(filepath)} ({len(self.raw_data)} rows)")
                
                print("CSV file loaded successfully!")
                print("========== End of load_csv_file ==========\n")
                return True
                
            except UnicodeDecodeError as e:
                error_msg = f"Failed to decode CSV file. Please check the file encoding.\nError: {str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                self.statusBar().showMessage("Error loading CSV file: encoding issue", 5000)
                print(f"UnicodeDecodeError: {str(e)}")
                
            except ValueError as e:
                error_msg = f"Failed to load CSV file: {str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                self.statusBar().showMessage("Error loading CSV file", 5000)
                print(f"ValueError: {str(e)}")
                
            except Exception as e:
                error_msg = f"An unexpected error occurred while loading the CSV file:\n{str(e)}"
                QMessageBox.critical(self, "Error", error_msg)
                self.statusBar().showMessage("Error loading CSV file", 5000)
                print(f"Unexpected error: {str(e)}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            error_msg = f"An error occurred before loading the CSV file:\n{str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.statusBar().showMessage("Error preparing to load CSV file", 5000)
            print(f"Error in load_csv_file: {str(e)}")
            import traceback
            traceback.print_exc()
            
        print("CSV file loading failed")
        print("========== End of load_csv_file (with errors) ==========\n")
        return False
    
    def update_raw_data_view(self):
        """Update the raw data table view with current data"""
        if self.raw_data is None or self.raw_data.empty:
            return
            
        # Prepare data for table model
        headers = self.raw_data.columns.tolist()
        data = [row.tolist() for _, row in self.raw_data.iterrows()]
        
        # Create table model
        self.raw_data_model = CustomTableModel(data, headers)
        
        # Create proxy model for filtering
        self.raw_data_proxy_model = QSortFilterProxyModel()
        self.raw_data_proxy_model.setSourceModel(self.raw_data_model)
        
        # Set the model on the table view
        self.raw_data_table.setModel(self.raw_data_proxy_model)
        
        # Enable sorting
        self.raw_data_table.setSortingEnabled(True)
        
        # Set column widths
        for i in range(len(headers)):
            self.raw_data_table.setColumnWidth(i, 150)
            
        # Update filter options
        if hasattr(self, 'column_selector'):
            self.column_selector.clear()
            self.column_selector.addItems(headers)
            self.update_filter_options()
    
    def analyze_data(self):
        """Process data and display analysis results"""
        if self.raw_data is not None:
            try:
                self.statusBar().showMessage("Analyzing data...")
                
                # Process data
                self.analysis_results = DataProcessor.analyze_data(self.raw_data)
                
                # Enable tabs
                self.tabs.setTabEnabled(2, True)
                self.tabs.setTabEnabled(3, True)
                
                # Update analysis view
                self.update_analysis_view()
                
                # Update chart
                self.update_chart()
                
                # Switch to analysis tab
                self.tabs.setCurrentIndex(2)
                
                self.statusBar().showMessage("Analysis complete", 5000)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to analyze data: {str(e)}")
                self.statusBar().showMessage("Error analyzing data", 5000)
    
    def update_analysis_view(self):
        """Update the analysis view based on selected analysis type"""
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            return
            
        selected_view = self.analysis_selector.currentText()
        
        if selected_view == "Player Total Scores":
            df = self.analysis_results['player_totals']
        elif selected_view == "Scores by Chest Type":
            df = self.analysis_results['chest_totals']
        elif selected_view == "Scores by Source":
            df = self.analysis_results['source_totals']
        elif selected_view == "Scores by Date":
            df = self.analysis_results['date_totals']
        elif selected_view == "Player Average Scores":
            df = self.analysis_results['player_avg']
        elif selected_view == "Chest Count by Player":
            df = self.analysis_results['player_counts']
        else:
            return
            
        # Prepare data for table model
        headers = df.columns.tolist()
        data = [row.tolist() for _, row in df.iterrows()]
        
        # Create and set up model
        model = CustomTableModel(data, headers)
        
        # Set model on table view
        self.analysis_view.setModel(model)
        
        # Set column widths
        for i in range(len(headers)):
            self.analysis_view.setColumnWidth(i, 150)
    
    def update_chart(self):
        """Update the chart based on current selections"""
        print("\n=== Starting update_chart ===")
        
        if self.analysis_results is None or not self.analysis_results:
            print("No analysis results available")
            return
            
        # Get selected parameters
        chart_type = self.chart_type_selector.currentText()
        x_column = self.chart_data_selector.currentText()
        
        # Auto-select the appropriate view based on x_column
        if x_column == "PLAYER":
            selected_view = "Player Total Scores"
        elif x_column == "CHEST":
            selected_view = "Scores by Chest Type"
        elif x_column == "SOURCE":
            selected_view = "Scores by Source"
        else:
            selected_view = self.analysis_selector.currentText()
        
        # Update the analysis selector to match our selection
        index = self.analysis_selector.findText(selected_view)
        if index >= 0:
            self.analysis_selector.setCurrentIndex(index)
        
        y_column = selected_view  # Use the view name as the y_column
        
        print(f"Chart parameters: type={chart_type}, x={x_column}, y={y_column}")
        print(f"Selected view: {selected_view}")
        
        if not x_column or not y_column:
            print("Missing x or y column selection")
            return
            
        # Clear previous chart
        self.mpl_canvas.axes.clear()
        
        try:
            # Get the appropriate DataFrame based on selected view
            print(f"Available analysis results keys: {list(self.analysis_results.keys())}")
            
            if selected_view == "Player Total Scores":
                data = self.analysis_results['player_totals']
            elif selected_view == "Scores by Chest Type":
                data = self.analysis_results['chest_totals']
            elif selected_view == "Scores by Source":
                data = self.analysis_results['source_totals']
            elif selected_view == "Scores by Date":
                data = self.analysis_results['date_totals']
            elif selected_view == "Player Average Scores":
                data = self.analysis_results['player_avg']
            elif selected_view == "Chest Count by Player":
                data = self.analysis_results['player_counts']
            else:
                print(f"Unknown view selection: {selected_view}")
                return
            
            # Debug: print DataFrame info
            print(f"DataFrame shape: {data.shape}")
            print(f"DataFrame columns: {data.columns.tolist()}")
            print(f"DataFrame sample:\n{data.head(3)}")
            
            # Check if the selected columns exist in the DataFrame
            if x_column not in data.columns:
                print(f"Error: x_column '{x_column}' not found in DataFrame columns")
                QMessageBox.warning(self, "Chart Error", f"Column '{x_column}' not found in the data")
                return
            
            # Make a copy to avoid modifying the original
            data = data.copy()
            
            print(f"Creating {chart_type} with x={x_column}, y={y_column}")
            
            # Handle different chart types
            if chart_type == "Bar Chart":
                print("Generating bar chart...")
                
                # If we're using SCORE as y value (implicit), explicitly select it
                y_column_actual = 'SCORE' if 'SCORE' in data.columns else 'COUNT'
                
                bars = data.plot(
                    kind='bar', 
                    x=x_column, 
                    y=y_column_actual, 
                    ax=self.mpl_canvas.axes,
                    color=self.mpl_canvas.chart_colors[0],
                    edgecolor=DARK_THEME['border'],
                    width=0.7
                )
                
                # Add value labels on top of bars
                for bar in bars.patches:
                    height = bar.get_height()
                    self.mpl_canvas.axes.text(
                        bar.get_x() + bar.get_width()/2.,
                        height + 0.02 * max(data[y_column_actual]),
                        f'{height:.1f}',
                        ha='center', 
                        va='bottom',
                        color=DARK_THEME['foreground'],
                        fontsize=9
                    )
                    
            elif chart_type == "Line Chart":
                print("Generating line chart...")
                
                # If we're using SCORE as y value (implicit), explicitly select it
                y_column_actual = 'SCORE' if 'SCORE' in data.columns else 'COUNT'
                
                data.plot(
                    kind='line', 
                    x=x_column, 
                    y=y_column_actual, 
                    ax=self.mpl_canvas.axes,
                    color=self.mpl_canvas.chart_colors[0],
                    marker='o',
                    markersize=5,
                    linewidth=2
                )
                
            elif chart_type == "Pie Chart":
                print("Generating pie chart...")
                
                # For pie charts, use SCORE or COUNT as values
                value_column = 'SCORE' if 'SCORE' in data.columns else 'COUNT'
                
                # Use all rows if we have a reasonable number, otherwise top 10
                if len(data) > 10:
                    print(f"Limiting pie chart to top 10 entries (total: {len(data)})")
                    chart_data = data.sort_values(value_column, ascending=False).head(10)
                else:
                    chart_data = data
                
                # Create a series for the pie chart
                pie_data = pd.Series(
                    chart_data[value_column].values, 
                    index=chart_data[x_column].values
                )
                
                wedges, texts, autotexts = self.mpl_canvas.axes.pie(
                    pie_data,
                    labels=None,  # We'll add a legend instead
                    autopct='%1.1f%%',
                    shadow=False,
                    startangle=90,
                    colors=self.mpl_canvas.chart_colors
                )
                
                # Enhance the appearance of percentage labels
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    autotext.set_weight('bold')
                
                # Add a legend
                self.mpl_canvas.axes.legend(
                    wedges, 
                    pie_data.index,
                    title=x_column,
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1)
                )
                
                self.mpl_canvas.axes.axis('equal')  # Equal aspect ratio ensures the pie is circular
            
            # Set chart title and labels
            view_title = selected_view.replace(" by ", "\nby ")
            self.mpl_canvas.axes.set_title(view_title, color=DARK_THEME['foreground'], fontsize=14)
            
            if chart_type != "Pie Chart":
                self.mpl_canvas.axes.set_xlabel(x_column, color=DARK_THEME['foreground'])
                
                # Set y label based on the view
                if "Count" in selected_view:
                    self.mpl_canvas.axes.set_ylabel("Count", color=DARK_THEME['foreground'])
                else:
                    self.mpl_canvas.axes.set_ylabel("Score", color=DARK_THEME['foreground'])
                
                # Add grid
                self.mpl_canvas.axes.grid(True, linestyle='--', alpha=0.7)
                
                # Rotate x tick labels if we have more than a few items
                if len(data) > 5:
                    self.mpl_canvas.axes.tick_params(axis='x', labelrotation=45)
            
            # Refresh the canvas
            self.mpl_canvas.figure.tight_layout()
            self.mpl_canvas.draw()
            
            print("Chart generated successfully")
            
        except Exception as e:
            error_msg = f"Error creating chart: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Chart Error", error_msg)
            
        print("=== Finished update_chart ===\n")
    
    def update_filter_options(self):
        """Update filter options based on selected column"""
        if self.raw_data is None or self.raw_data.empty or self.column_selector.currentText() == "":
            return
            
        column = self.column_selector.currentText()
        unique_values = sorted(self.raw_data[column].unique())
        
        # Update filter combobox
        self.value_selector.clear()
        self.value_selector.addItem("All")  # Option to show all
        self.value_selector.addItems([str(val) for val in unique_values])
    
    def filter_raw_data(self):
        """Filter raw data based on selected criteria"""
        if self.raw_data is None or self.raw_data.empty or self.column_selector.currentText() == "":
            return
            
        filter_text = self.value_selector.currentText()
        column_index = self.column_selector.currentIndex()
        
        # If "All" selected, clear filter
        if filter_text == "All":
            # Use the current API for clearing filters in PySide6
            self.raw_data_proxy_model.setFilterFixedString("")
            return
        
        # Apply filter
        self.raw_data_proxy_model.setFilterKeyColumn(column_index)
        self.raw_data_proxy_model.setFilterFixedString(filter_text)
    
    def export_current_analysis(self):
        """Export the current analysis view to a CSV file"""
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            QMessageBox.warning(self, "Warning", "No analysis data available to export.")
            return
            
        # Get current view
        selected_view = self.analysis_selector.currentText().replace(" ", "_").lower()
        
        # Determine which DataFrame to export
        if selected_view == "player_total_scores":
            df = self.analysis_results['player_totals']
            default_filename = "player_total_scores.csv"
        elif selected_view == "scores_by_chest_type":
            df = self.analysis_results['chest_totals']
            default_filename = "scores_by_chest_type.csv"
        elif selected_view == "scores_by_source":
            df = self.analysis_results['source_totals']
            default_filename = "scores_by_source.csv"
        elif selected_view == "scores_by_date":
            df = self.analysis_results['date_totals']
            default_filename = "scores_by_date.csv"
        elif selected_view == "player_average_scores":
            df = self.analysis_results['player_avg']
            default_filename = "player_average_scores.csv"
        elif selected_view == "chest_count_by_player":
            df = self.analysis_results['player_counts']
            default_filename = "chest_count_by_player.csv"
        else:
            default_filename = "chest_count_by_player.csv"
        
        # Get export directory from config
        export_dir = self.config_manager.get_export_directory()
        
        # Create full path for default filename
        default_path = os.path.join(export_dir, default_filename)
        
        # Ask for save location
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis", default_path, "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                # Save the directory for next time
                self.config_manager.set('General', 'export_directory', str(Path(filepath).parent))
                
                df.to_csv(filepath, index=False)
                self.statusBar().showMessage(f"Exported to {filepath}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
                self.statusBar().showMessage("Error exporting data", 5000)

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    # Apply dark theme
    StyleManager.apply_dark_theme(app)
    
    # Create MainWindow
    window = MainWindow()
    
    # Show the window
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

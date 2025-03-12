# utils.py - Utility functions and constants
import sys
import os
import csv
import pandas as pd
import numpy as np
import configparser
import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import traceback
import matplotlib
matplotlib.use('QtAgg')  # Use the generic Qt backend that works with PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import types  # Add this import for method binding
import re  # Add this import for regular expressions
import time
import json
import random
from datetime import datetime, timedelta
import tempfile

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QPushButton, QTabWidget, QLabel, QFileDialog,
    QComboBox, QGroupBox, QSplitter, QMessageBox, QFrame, QHeaderView,
    QLineEdit, QListWidget, QDateEdit, QCheckBox, QListWidgetItem,
    QGridLayout, QTextBrowser
)
from PySide6.QtPrintSupport import QPrinter, QPageSetupDialog
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, Signal, QMimeData, 
    QUrl, QSize, Slot, QSortFilterProxyModel, QObject, QEvent, QTimer,
    QSettings, QStandardPaths, QDate
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QDropEvent, QDragEnterEvent,
    QColor, QPalette, QFont, QIcon, QPixmap, QPainter
)

# Global constants
TABLEAU_COLORS = ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab']

# Dark theme definition
DARK_THEME = {
    'background': '#1A2742',  # Dark blue background similar to Total Battle
    'foreground': '#FFFFFF',  # White text for better contrast
    'accent': '#D4AF37',      # Brighter gold accent for lines and small highlights
    'accent_hover': '#F0C75A',  # Lighter gold for hover states
    'background_light': '#2A3752',  # Slightly lighter background for cards
    'card_bg': '#2A3752',     # Card background
    'header_bg': '#141E36',   # Darker blue for headers
    'border': '#3A4762',      # Border color
    'text_disabled': '#8899AA',  # Disabled text
    'button_gradient_top': '#D4AF37',  # Button gradient top
    'button_gradient_bottom': '#B28E1C',  # Button gradient bottom
    'button_hover': '#F0C75A',  # Button hover state
    'button_active': '#A37F18',  # Button active/pressed state
    'button_disabled': '#5A6A7A',  # Disabled button
    'input_bg': '#2A3752',    # Input field background
    'input_border': '#3A4762',  # Input field border
    'input_focus': '#D4AF37',  # Input field focus border
    'scrollbar_bg': '#1A2742',  # Scrollbar background
    'scrollbar_handle': '#3A4762',  # Scrollbar handle
    'scrollbar_handle_hover': '#4A5772',  # Scrollbar handle hover
    'tooltip_bg': '#141E36',  # Tooltip background
    'tooltip_border': '#D4AF37',  # Tooltip border
    'selection_bg': '#D4AF37',  # Selection background
    'selection_fg': '#1A2742',  # Selection text color
    'link': '#D4AF37',        # Link color
    'link_hover': '#F0C75A',  # Link hover color
    'success': '#59a14f',     # Success color
    'warning': '#f28e2c',     # Warning color
    'error': '#e15759',       # Error color
    'info': '#76b7b2'         # Info color
}

def log_error(error_message, exception=None, show_traceback=True):
    """Centralized error handling function to log errors consistently.
    
    Args:
        error_message (str): The error message to display
        exception (Exception, optional): The exception object. Defaults to None.
        show_traceback (bool, optional): Whether to print the traceback. Defaults to True.
    """
    if exception:
        print(f"{error_message}: {str(exception)}")
    else:
        print(error_message)
        
    if show_traceback:
        traceback.print_exc()

def exception_handler(exctype, value, tb):
    """Global exception handler for the application."""
    print(f"Unhandled exception: {exctype.__name__}: {value}")
    traceback.print_tb(tb)

    # Show error dialog
    error_msg = QMessageBox()
    error_msg.setIcon(QMessageBox.Critical)
    error_msg.setWindowTitle("Error")
    error_msg.setText(f"An error occurred: {exctype.__name__}")
    error_msg.setInformativeText(str(value))
    error_msg.setDetailedText(''.join(traceback.format_tb(tb)))
    error_msg.setStandardButtons(QMessageBox.Ok)
    error_msg.exec()

# Set up global exception handler
sys.excepthook = exception_handler

class ConfigManager:
    """Manage application configuration settings."""

    def __init__(self, app_name="TotalBattleAnalyzer"):
        """
        Initialize the configuration manager.

        Args:
        app_name (str): The name of the application.
        """
        self.app_name = app_name
        self.config = {}
        self.config_dir = os.path.join(os.path.expanduser("~"), f".{app_name.lower()}")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load the configuration
        self.load_config()
        
    @staticmethod
    def load_config():
        """
        Static method to load configuration from file.

        Returns:
        dict: A dictionary with configuration settings.
        """
        # Default configuration
        default_config = {
        'theme': 'dark',
        'window_size': (1200, 800),
        'recent_files': [],
        'max_recent_files': 5,
        'import_dir': os.path.join(os.getcwd(), 'import'),
        'export_dir': os.path.join(os.getcwd(), 'exports'),
        'encodings': ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-8-sig']
        }
        
        # Return default config
        return default_config
    
    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            log_error(f"Error saving config file: {str(e)}", e)

    def get(self, section, key, default=None):
        """
        Get a configuration value.
        
        Args:
        section (str): The section name.
        key (str): The key within the section."""
        section_dict = self.config.get(section, {})
        return section_dict.get(key, default)

    def add_recent_file(self, filepath):
        """
        Add a file to the recent files list.

        Args:
        filepath (str): The path to the file.
        """
        if 'recent_files' not in self.config:
            self.config['recent_files'] = []
        
        # Remove if already exists
        if filepath in self.config['recent_files']:
            self.config['recent_files'].remove(filepath)
        
        # Add to the beginning
        self.config['recent_files'].insert(0, filepath)
        
        # Limit the number of recent files
        max_recent = self.config.get('max_recent_files', 5)
        if len(self.config['recent_files']) > max_recent:
            self.config['recent_files'] = self.config['recent_files'][:max_recent]
        
        self.save_config()
    
    def get_recent_files(self):
        """
        Get the list of recent files.

        Returns:
        list: A list of recent file paths.
        """
        return self.config.get('recent_files', [])
    
    def set_theme(self, theme):
        """
        Set the theme.

        Args:
        theme (str): The theme name.
        """
        self.config['theme'] = theme
        self.save_config()
    
    def get_theme(self):
        """
        Get the current theme.

        Returns:
        str: The theme name.
        """
        return self.config.get('theme', 'dark')
    
    def set_window_size(self, width, height):
        """
        Set the window size.

        Args:
        width (int): The window width.
        height (int): The window height.
        """
        self.config['window_size'] = (width, height)
        self.save_config()
    
    def get_window_size(self):
        """
        Get the window size.

        Returns:
        tuple: A tuple of (width, height).
        """
        return self.config.get('window_size', (1200, 800))
    
    def set_import_directory(self, directory):
        """
        Set the import directory.

        Args:
        directory (str): The directory path.
        """
        self.config['import_dir'] = directory
        self.save_config()
    
    def get_import_directory(self):
        """
        Get the import directory.

        Returns:
        str: The import directory path.
        """
        return self.config.get('import_dir', os.path.join(os.getcwd(), 'import'))
    
    def set_export_directory(self, directory):
        """
        Set the export directory.

        Args:
        directory (str): The directory path.
        """
        self.config['export_dir'] = directory
        self.save_config()
    
    def get_export_directory(self):
        """
        Get the export directory.

        Returns:
        str: The export directory path.
        """
        return self.config.get('export_dir', os.path.join(os.getcwd(), 'exports'))


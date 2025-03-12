#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Total Battle Analyzer application.

This file initializes the application, sets up the main window,
and handles high-level configuration and error handling.
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Import PySide6 components
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QDir, QSettings
from PySide6.QtGui import QIcon

# Import custom modules
from modules.utils import log_error
from modules.configmanager import ConfigManager
from modules.stylemanager import StyleManager
from modules.mainwindow import MainWindow

def create_directories():
    """Create necessary directories for the application."""
    # Create data directory and subdirectories
    data_dir = Path('data')
    import_dir = Path('data/imports')
    export_dir = Path('data/exports')
    temp_dir = Path('temp')
    
    for directory in [data_dir, import_dir, export_dir, temp_dir]:
        if not directory.exists():
            try:
                directory.mkdir(parents=True)
                print(f"Created directory: {directory.absolute()}")
            except Exception as e:
                print(f"Error creating directory {directory}: {e}")

def exception_handler(exctype, value, tb):
    """Global exception handler for unhandled exceptions."""
    error_msg = f"Unhandled exception: {exctype.__name__}: {value}"
    traceback.print_tb(tb)
    
    # Show error dialog
    if QApplication.instance():
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(f"An error occurred: {exctype.__name__}")
        error_dialog.setInformativeText(str(value))
        error_dialog.setDetailedText("".join(traceback.format_tb(tb)))
        error_dialog.exec_()
    
    # Log error
    log_error(error_msg, value, show_traceback=True)
    
    # Call the default exception handler
    sys.__excepthook__(exctype, value, tb)

def main():
    """Main entry point for the application."""
    try:
        # Set up exception handler
        sys.excepthook = exception_handler
        
        # Create necessary directories
        create_directories()
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Total Battle Analyzer")
        app.setOrganizationName("TotalBattleTools")
        
        # Set application icon
        icon_path = Path(__file__).parent / 'resources' / 'icon.png'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create main window
        main_window = MainWindow("Total Battle Analyzer")
        
        # Apply theme based on configuration
        theme = main_window.config_manager.get_theme()
        StyleManager.apply_dark_theme(app)
        # Show main window
        main_window.show()

        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()

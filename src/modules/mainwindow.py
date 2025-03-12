#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main window class for the Total Battle Analyzer application.

This class manages the application's main window, including the UI elements,
data processing, analysis, and visualization.
"""

import os
import sys
import json
import csv
import traceback
import tempfile
import datetime
from pathlib import Path
import re

# Data manipulation and visualization
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Qt imports
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QTableView, QTabWidget, QSplitter, QFrame,
    QComboBox, QLineEdit, QGroupBox, QCheckBox, QListWidget, QHeaderView,
    QAbstractItemView, QDateEdit, QTextBrowser, QApplication,
    QListWidgetItem, QStatusBar, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate, QSettings, QDir, Signal, QSortFilterProxyModel
from PySide6.QtGui import QIcon, QColor
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# Import custom modules
from .utils import log_error
from .stylemanager import StyleManager, DARK_THEME
from .configmanager import ConfigManager
from .customtablemodel import CustomTableModel
from .mplcanvas import MplCanvas
from .droparea import DropArea
from .importarea import ImportArea
from .dataprocessor import DataProcessor
from .filterarea import FilterArea

class MainWindow(QMainWindow):
    """
    Main window of the Total Battle Analyzer application.
    Provides functionality for importing, filtering, and visualizing chest data.
    """
    
    def __init__(self, title="Total Battle Analyzer", debug=False):
        """
        Initialize the main window.
        
        Args:
            title (str, optional): Window title. Defaults to "Total Battle Analyzer".
            debug (bool, optional): Enable debug output. Defaults to False.
        """
        super().__init__()
        self.title = title
        self.debug = debug
        
        # Initialize configuration
        self.config_manager = ConfigManager(title)
        
        # Initialize data storage
        self.raw_data = None
        self.processed_data = None
        
        # Set up directories
        self.import_dir = Path(self.config_manager.get_import_directory())
        self.export_dir = Path(self.config_manager.get_export_directory())
        
        # Create directories if they don't exist
        os.makedirs(self.import_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Set window size from config
        width, height = self.config_manager.get_window_size()
        self.resize(width, height)
        
        # Apply theme
        theme = self.config_manager.get_theme()
        StyleManager.apply_dark_theme(QApplication.instance())
        
        # Set up the UI
        self._setup_ui()
        
        # Connect signals
        self.drop_area.fileDropped.connect(self.load_csv_file)
        self.import_area.fileSelected.connect(self.load_csv_file)
        
        if self.debug:
            print("MainWindow initialized")
    
    def show_error_dialog(self, title, message):
        """
        Show an error dialog with the specified title and message.
        
        Args:
            title (str): The title of the error dialog.
            message (str): The message to display.
        """
        QMessageBox.critical(self, title, message)

    def init_tab_states(self):
        """Initialize the states of all tabs."""
        # This method is called after UI setup to initialize any tab-specific states or data
        
        # Initialize Raw Data tab
        if hasattr(self, 'column_selector'):
            self.column_selector.clear()
            
        # Make sure value selection panel is properly shown/hidden
        if hasattr(self, 'show_value_selection') and hasattr(self, 'value_list_widget'):
            is_checked = self.show_value_selection.isChecked()
            self.value_list_widget.setVisible(is_checked)
            
        # Initialize Analysis tab
        if hasattr(self, 'analysis_column_selector'):
            self.analysis_column_selector.clear()
            
        # Make sure analysis value panel is properly shown/hidden
        if hasattr(self, 'analysis_show_value_selection') and hasattr(self, 'analysis_value_panel'):
            is_checked = self.analysis_show_value_selection.isChecked()
            self.analysis_value_panel.setVisible(is_checked)
            
        # Initialize Charts tab
        if hasattr(self, 'chart_type_selector') and hasattr(self, 'chart_data_selector'):
            # Set default chart type and data
            self.chart_type_combo.setCurrentIndex(0)
            
        # Initialize Reports tab
        if hasattr(self, 'report_type_selector'):
            self.report_type_selector.setCurrentIndex(0)
        
        # Set status message
        self.statusBar().showMessage("Ready")

    def load_csv_file(self, filepath):
        """
        Load data from a CSV file.
        
        This method attempts to load a CSV file with various encodings and separators,
        handling potential errors gracefully. It updates the UI components with the
        loaded data and enables relevant functionality.
        
        Args:
            filepath (str): Path to the CSV file to load
        """
        try:
            # Store the current file path
            self.current_file = filepath
            
            # Update file label
            self.file_label.setText(f"Loading: {os.path.basename(filepath)}")
            self.statusBar().showMessage(f"Loading {os.path.basename(filepath)}...")
            
            # Define encodings to try, prioritizing German-friendly encodings
            encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'iso-8859-1', 'latin1']
            
            # Try to detect encoding by reading a sample
            sample_size = 4096  # Increased from 1KB to 4KB for better detection
            encoding_detected = None
            
            try:
                with open(filepath, 'rb') as f:
                    raw_data = f.read(sample_size)
                    
                # Check for UTF-8 BOM
                if raw_data.startswith(b'\xef\xbb\xbf'):
                    encoding_detected = 'utf-8-sig'
                    if self.debug:
                        print(f"Detected UTF-8 with BOM")
                # Check for German umlauts in UTF-8
                elif re.search(rb'[\xc3][\xa4\xb6\xbc\x84\x96\x9c\x9f]', raw_data):  # ä, ö, ü, Ä, Ö, Ü, ß
                    encoding_detected = 'utf-8'
                    if self.debug:
                        print(f"Detected UTF-8 encoding based on umlaut pattern")
                # Check for German umlauts in ISO/Windows encodings
                elif re.search(rb'[\xe4\xf6\xfc\xc4\xd6\xdc\xdf]', raw_data):  # ä, ö, ü, Ä, Ö, Ü, ß
                    encoding_detected = 'cp1252'
                    if self.debug:
                        print(f"Detected Windows-1252 encoding based on umlaut pattern")
                    
                if self.debug:
                    print(f"Raw data sample: {raw_data[:100]}")
                    if encoding_detected:
                        print(f"Detected encoding: {encoding_detected} based on content analysis")
            except Exception as e:
                if self.debug:
                    print(f"Error during encoding detection: {e}")
            
            # If encoding was detected, try it first
            if encoding_detected:
                encodings.remove(encoding_detected)
                encodings.insert(0, encoding_detected)
                if self.debug:
                    print(f"Trying detected encoding first: {encoding_detected}")
            
            # Try each encoding
            df = None
            errors = []
            
            for encoding in encodings:
                try:
                    if self.debug:
                        print(f"Trying encoding: {encoding}")
                    
                    # Read with pandas, handle German date format
                    df = pd.read_csv(filepath, encoding=encoding, parse_dates=['DATE'], dayfirst=True)
                    
                    # Verify that umlauts are readable by checking a sample
                    if self.debug and 'PLAYER' in df.columns:
                        players = df['PLAYER'].head(5).tolist()
                        print(f"Sample players with {encoding}: {players}")
                        
                        # Test if umlauts are correctly encoded
                        for player in players:
                            if 'ä' in player or 'ö' in player or 'ü' in player:
                                print(f"Found umlauts in player name: {player}")
                    
                    # If encoding works, break the loop
                    break
                    
                except UnicodeDecodeError as e:
                    errors.append(f"Failed with {encoding}: {str(e)}")
                    continue
                except Exception as e:
                    errors.append(f"Error with {encoding}: {str(e)}")
                    continue
            
            if df is None:
                raise ValueError(f"Failed to load file with any encoding.\nTried:\n" + "\n".join(errors))
            
            # Check for required columns (case-insensitive)
            required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
            df_columns_upper = [col.upper() for col in df.columns]
            missing_columns = [col for col in required_columns if col not in df_columns_upper]
            
            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {', '.join(missing_columns)}\n\n"
                    "Required columns are:\n"
                    "DATE, PLAYER, SOURCE, CHEST, SCORE"
                )
            
            # Create mapping from actual column names to standardized names
            column_mapping = {}
            for req_col in required_columns:
                for actual_col in df.columns:
                    if actual_col.upper() == req_col:
                        column_mapping[actual_col] = req_col
            
            # Rename columns to standardized names
            df = df.rename(columns=column_mapping)
            
            # Convert SCORE to numeric, handling German number format
            df['SCORE'] = pd.to_numeric(df['SCORE'].astype(str).str.replace(',', '.'), errors='coerce')
            df = df.dropna(subset=['SCORE'])
            
            # Ensure DATE is datetime
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            df = df.dropna(subset=['DATE'])
            
            # Keep only required columns and any additional columns
            required_plus_extras = required_columns + [col for col in df.columns if col not in required_columns]
            df = df[required_plus_extras]
            
            # Store the data
            self.raw_data = df
            self.processed_data = df.copy()
            
            # Update Raw Data tab filter options
            if hasattr(self, 'column_selector'):
                if self.debug:
                    print("Populating column_selector with columns:", df.columns.tolist())
                self.column_selector.clear()
                self.column_selector.addItems(df.columns.tolist())
                # Update filter options based on the first column
                if df.columns.size > 0:
                    self.update_filter_options()
            
            # Update Analysis tab filter options
            if hasattr(self, 'analysis_column_selector'):
                if self.debug:
                    print("Populating analysis_column_selector with columns:", df.columns.tolist())
                self.analysis_column_selector.clear()
                self.analysis_column_selector.addItems(df.columns.tolist())
                # Update filter options based on the first column
                if df.columns.size > 0:
                    self.update_analysis_filter_options()
            
            # Update visibility of filter panels
            if hasattr(self, 'show_value_selection'):
                is_checked = self.show_value_selection.isChecked()
                if self.debug:
                    print(f"Setting value selection visibility: {is_checked}")
                self.toggle_value_selection(is_checked)
            
            if hasattr(self, 'analysis_show_value_selection'):
                is_checked = self.analysis_show_value_selection.isChecked()
                if self.debug:
                    print(f"Setting analysis value selection visibility: {is_checked}")
                self.toggle_analysis_value_selection(is_checked)
            
            # Create and set table model for raw data tab
            model = CustomTableModel(df)
            self.raw_data_table.setModel(model)
            
            # Update analysis view
            self.update_analysis_view()
            
            # Update chart
            self.update_chart()
            
            # Add to recent files
            self.config_manager.add_recent_file(filepath)
            
            # Update import directory
            self.config_manager.set_import_directory(str(Path(filepath).parent))
            
            # Update file label and status
            self.file_label.setText(f"Loaded: {os.path.basename(filepath)}")
            self.statusBar().showMessage(
                f"Loaded {len(df)} records from {os.path.basename(filepath)} using {encoding_detected or encoding} encoding"
            )
            
            if self.debug:
                print(f"Successfully loaded file: {filepath}")
                print(f"Using encoding: {encoding_detected or encoding}")
                print(f"Columns: {df.columns.tolist()}")
                print(f"Shape: {df.shape}")
            
        except Exception as e:
            error_msg = f"Failed to load CSV file: {str(e)}"
            if self.debug:
                print(error_msg)
            traceback.print_exc()
            self.file_label.setText("No file loaded")
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def apply_filter(self):
        """Apply the current filter settings to the data"""
        if self.raw_data is None:
            return
        
        try:
            # Get filter settings
            settings = self.filter_area.get_filter_settings()
            
            # Start with raw data
            filtered_data = self.raw_data.copy()
            
            # Apply date filter if enabled
            if settings['date_filter_enabled'] and 'DATE' in filtered_data.columns:
                filtered_data['DATE'] = pd.to_datetime(filtered_data['DATE'])
                start_date = pd.to_datetime(settings['start_date'])
                end_date = pd.to_datetime(settings['end_date'])
                filtered_data = filtered_data[
                    (filtered_data['DATE'] >= start_date) &
                    (filtered_data['DATE'] <= end_date)
                ]
            
            # Apply value filter if enabled
            if settings['value_filter_enabled'] and settings['column'] in filtered_data.columns:
                selected_values = settings['selected_values']
                if selected_values:
                    filtered_data = filtered_data[
                        filtered_data[settings['column']].astype(str).isin(selected_values)
                    ]
                    status_message = f"Filtered by {settings['column']}: {len(selected_values)} values selected"
                else:
                    # No values selected - show warning
                    self.statusBar().showMessage("Warning: No values selected for filtering")
                    return
            else:
                status_message = "No value filter applied"
            
            # Update processed data
            self.processed_data = filtered_data
            
            # Update table model
            model = CustomTableModel(filtered_data)
            self.raw_data_table.setModel(model)
            
            # Update chart
            self.update_chart()
            
            # Update status
            self.statusBar().showMessage(
                f"{status_message} - {len(filtered_data)} rows (from {len(self.raw_data)} total)"
            )
            
            if self.debug:
                print("Filter applied with settings:", settings)
                print(f"Filtered data shape: {filtered_data.shape}")
        except Exception as e:
            if self.debug:
                print(f"Error applying filter: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to apply filter: {str(e)}")

    def clear_filter(self):
        """Clear all filters and show raw data"""
        if self.raw_data is None:
            return
        
        try:
            # Reset processed data to raw data
            self.processed_data = self.raw_data.copy()
            
            # Update table model
            model = CustomTableModel(self.raw_data)
            self.raw_data_table.setModel(model)
            
            # Update chart
            self.update_chart()
            
            # Update status
            self.statusBar().showMessage("Filters cleared")
            
            if self.debug:
                print("Filters cleared")
        except Exception as e:
            if self.debug:
                print(f"Error clearing filters: {e}")
            QMessageBox.warning(self, "Warning", f"Failed to clear filters: {str(e)}")

    def update_chart(self):
        """Update the chart based on the current data and chart type"""
        if self.processed_data is None or self.mpl_canvas is None:
            return
        
        try:
            # Clear the current chart
            self.mpl_canvas.axes.clear()
            
            # Get the selected chart type
            chart_type = self.chart_type_combo.currentText()
            
            # Define required columns based on chart type
            required_columns = {
                "Player Totals": ["PLAYER", "SCORE"],
                "Chest Totals": ["CHEST", "SCORE"],
                "Source Totals": ["SOURCE", "SCORE"],
                "Date Totals": ["DATE", "SCORE"]
            }
            
            # Check if required columns are present
            if chart_type not in required_columns:
                self.mpl_canvas.axes.text(
                    0.5, 0.5, "Invalid chart type selected",
                    ha='center', va='center'
                )
                self.mpl_canvas.draw()
                return
            
            columns = required_columns[chart_type]
            missing_columns = set(columns) - set(self.processed_data.columns)
            
            if missing_columns:
                self.mpl_canvas.axes.text(
                    0.5, 0.5, f"Missing required columns: {', '.join(missing_columns)}",
                    ha='center', va='center'
                )
                self.mpl_canvas.draw()
                self.statusBar().showMessage(f"Cannot create chart: missing columns {missing_columns}")
                return
            
            # Group data based on chart type
            if chart_type == "Date Totals":
                # Convert DATE to datetime if it's not already
                self.processed_data['DATE'] = pd.to_datetime(self.processed_data['DATE'])
                grouped_data = self.processed_data.groupby('DATE')['SCORE'].sum()
                grouped_data = grouped_data.sort_index()
                
                # Create line plot
                self.mpl_canvas.axes.plot(
                    grouped_data.index, grouped_data.values,
                    marker='o', linestyle='-', linewidth=2
                )
                self.mpl_canvas.axes.set_xlabel("Date")
            else:
                # Group by the appropriate column
                group_col = chart_type.split()[0].upper()
                grouped_data = self.processed_data.groupby(group_col)['SCORE'].sum()
                grouped_data = grouped_data.sort_values(ascending=False)
                
                # Create bar plot
                grouped_data.plot(
                    kind='bar',
                    ax=self.mpl_canvas.axes,
                    color=self.mpl_canvas.style_presets['default']['bar_colors']
                )
                self.mpl_canvas.axes.set_xlabel(group_col)
            
            # Set labels and title
            self.mpl_canvas.axes.set_ylabel("Score")
            self.mpl_canvas.axes.set_title(chart_type)
            
            # Rotate x-axis labels for better readability
            self.mpl_canvas.axes.tick_params(axis='x', rotation=45)
            
            # Adjust layout to prevent label cutoff
            self.mpl_canvas.fig.tight_layout()
            
            # Draw the updated chart
            self.mpl_canvas.draw()
            
            if self.debug:
                print(f"Updated chart: {chart_type}")
        except Exception as e:
            if self.debug:
                print(f"Error updating chart: {e}")
            self.mpl_canvas.axes.clear()
            self.mpl_canvas.axes.text(
                0.5, 0.5, f"Error creating chart: {str(e)}",
                ha='center', va='center'
            )
            self.mpl_canvas.draw()
            QMessageBox.warning(self, "Warning", f"Failed to update chart: {str(e)}")

    def process_data(self):
        """Process the loaded data to prepare it for analysis and visualization."""
        if self.data is None:
            print("No data to process")
            return
        
        try:
            print("Starting data processing...")
            # Make a copy of the data
            df = self.data.copy()
            
            # Check for required columns
            required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
            
            print(f"Available columns: {list(df.columns)}")
            
            # Check if all required columns exist (case-insensitive)
            df_columns_upper = [col.upper() for col in df.columns]
            missing_columns = [col for col in required_columns if col not in df_columns_upper]
            
            if missing_columns:
                # Show error message
                missing_cols_str = ", ".join(missing_columns)
                error_msg = f"Missing required columns: {missing_cols_str}"
                print(error_msg)
                self.statusBar().showMessage(error_msg)
                
                QMessageBox.critical(
                    self,
                    "Missing Required Columns",
                    f"The CSV file is missing the following required columns: {missing_cols_str}\n\n"
                    "Please ensure your CSV file has the following columns:\n"
                    "DATE, PLAYER, SOURCE, CHEST, SCORE"
                )
                return
            
            # Create a mapping from actual column names to standardized names
            column_mapping = {}
            for req_col in required_columns:
                for actual_col in df.columns:
                    if actual_col.upper() == req_col:
                        column_mapping[actual_col] = req_col
            
            print(f"Column mapping: {column_mapping}")
            
            # Rename columns to standardized names
            df = df.rename(columns=column_mapping)
            
            print("Converting SCORE to numeric...")
            # Convert SCORE to numeric
            df['SCORE'] = pd.to_numeric(df['SCORE'], errors='coerce')
            
            # Drop rows with NaN SCORE
            df = df.dropna(subset=['SCORE'])
            
            print("Converting DATE to datetime...")
            # Convert DATE to datetime
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            
            # Drop rows with invalid dates
            df = df.dropna(subset=['DATE'])
            
            # Keep only the required columns
            df = df[required_columns]
            
            print(f"Processed data shape: {df.shape}")
            print("Sample of processed data:")
            print(df.head())
            
            # Store the processed data
            self.processed_data = df
            
            # Update the column selector
            if hasattr(self, 'column_selector'):
                print("Updating column selector...")
                self.column_selector.clear()
                self.column_selector.addItems(df.columns.tolist())
            
            # Update the raw data table
            if hasattr(self, 'raw_data_table'):
                print("Updating raw data table...")
                model = CustomTableModel(df)
                self.raw_data_table.setModel(model)
            
            # Update status
            self.statusBar().showMessage(f"Processed {len(df)} records")
            
            # Analyze the data
            print("Analyzing data...")
            self.analyze_data()
            
        except Exception as e:
            print(f"Error in process_data: {str(e)}")
            self.statusBar().showMessage(f"Error processing data: {str(e)}")
            log_error("Error processing data", e, show_traceback=True)
            
            # Show error message
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error Processing Data")
            error_msg.setText(f"Error processing data: {str(e)}")
            error_msg.setDetailedText(traceback.format_exc())
            error_msg.exec_()

    def update_raw_data_table(self):
        """Update the raw data table with the processed data."""
        if self.processed_data is None:
            return
            
        # Create a model for the raw data table
        model = CustomTableModel(self.processed_data)
        self.raw_data_table.setModel(model)
        
        # Resize columns to content
        self.raw_data_table.resizeColumnsToContents()
        
        # Update column selector in the filter panel
        self.column_selector.clear()
        self.column_selector.addItems(self.processed_data.columns.tolist())

    def filter_raw_data(self):
        """Apply filters to the raw data table."""
        if self.raw_data is None:
            return
            
        filtered_data = self.raw_data.copy()
        
        try:
            # Get the current filter state
            column_name = self.column_selector.currentText()
            date_filter_enabled = self.date_filter_enabled.isChecked()
            value_selection_enabled = self.show_value_selection.isChecked()
            
            # If value selection is enabled, use selected items
            if value_selection_enabled:
                selected_items = self.value_list.selectedItems()
                if selected_items:
                    selected_values = [item.text() for item in selected_items]
                    filtered_data = filtered_data[filtered_data[column_name].astype(str).isin(selected_values)]
                    
                    # Show status message about column filtering
                    status_message = f"Filtered by {column_name}: {len(selected_values)} values selected"
                else:
                    # No column filter applied (no values selected)
                    status_message = "Warning: No values selected for filtering - no results"
                    QMessageBox.warning(self, "Filter Warning", "No values are selected. Please select at least one value.")
                    return
            else:
                # Value selection is not enabled - using all values
                status_message = f"Using all values for {column_name}"
            
            # Apply date filter if enabled
            if date_filter_enabled and 'DATE' in filtered_data.columns:
                start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
                end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
                
                # Convert to datetime for filtering
                start_date_dt = pd.to_datetime(start_date)
                end_date_dt = pd.to_datetime(end_date)
                
                # Make sure DATE is datetime
                filtered_data['DATE'] = pd.to_datetime(filtered_data['DATE'])
                
                # Filter by date range
                filtered_data = filtered_data[(filtered_data['DATE'] >= start_date_dt) & 
                                             (filtered_data['DATE'] <= end_date_dt)]
                
                status_message += f", date range: {start_date} to {end_date}"
            
            # Update the table with filtered data
            model = CustomTableModel(filtered_data)
            self.raw_data_table.setModel(model)
            
            # Store as processed data
            self.processed_data = filtered_data
            
            # Update status
            self.statusBar().showMessage(f"{status_message} - {len(filtered_data)} records")
            
        except Exception as e:
            error_msg = f"Error filtering data: {str(e)}"
            self.statusBar().showMessage(error_msg)
            
            if self.debug:
                print(error_msg)
                traceback.print_exc()
            
            QMessageBox.warning(self, "Filter Error", error_msg)

    def clear_filters(self):
        """Clear all filters and reset the raw data table."""
        if self.processed_data is None:
            return
            
        # Reset filter values
        self.filter_value.clear()
        self.date_filter_enabled.setChecked(False)
        
        # If value selection is enabled, clear selections
        if hasattr(self, 'value_list') and self.show_value_selection.isChecked():
            self.value_list.clearSelection()
        
        # Update the table with the full dataset
        model = CustomTableModel(self.processed_data)
        self.raw_data_table.setModel(model)
        
        self.statusBar().showMessage(f"Cleared filters: {len(self.processed_data)} records")

    def toggle_value_selection(self, state):
        """Toggle the visibility of the value selection panel."""
        # Handle different parameter types
        if isinstance(state, bool):
            is_visible = state
        elif state is None:
            # If None, use the current checkbox state
            is_visible = self.show_value_selection.isChecked()
        else:
            # Assume it's a Qt.CheckState value
            is_visible = state == Qt.Checked
        
        if self.debug:
            print(f"Toggle value selection: state={state}, is_visible={is_visible}")
        
        # Set visibility
        if hasattr(self, 'value_list_widget'):
            self.value_list_widget.setVisible(is_visible)
            
            # Update filter options if now visible
            if is_visible:
                if self.debug:
                    print("Calling update_filter_options")
                self.update_filter_options()
    
    def update_filter_options(self):
        """Update the available filter options based on the selected column."""
        if not hasattr(self, 'value_list') or self.raw_data is None:
            return
            
        column = self.column_selector.currentText()
        if not column:
            return
            
        # Clear the list
        self.value_list.clear()
        
        # Get unique values from the selected column
        unique_values = self.raw_data[column].astype(str).unique().tolist()
        unique_values.sort()
        
        # Add the unique values to the analysis value list
        for value in unique_values:
            item = QListWidgetItem(value)
            self.value_list.addItem(item)
            
        # Select all values by default
        self.select_all_values()
        
        if self.debug:
            print(f"Added {len(unique_values)} unique values to value_list for column {column}")
    
    def analyze_data(self):
        """Analyze the processed data and prepare it for the analysis tab."""
        if self.processed_data is None:
            return
            
        # Update the analysis view based on the selected analysis type
        self.update_analysis_view()
        
        # Update the chart if the chart selector exists
        if hasattr(self, 'chart_type_selector') and hasattr(self, 'mpl_canvas'):
            self.update_chart()

    def update_analysis_view(self):
        """Update the analysis view based on the selected analysis type."""
        if not hasattr(self, 'processed_data') or self.processed_data is None:
            # Create an empty DataFrame with a message
            result = pd.DataFrame({"Message": ["No data loaded. Please import a CSV file."]})
            model = CustomTableModel(result)
            self.analysis_view.setModel(model)
            self.statusBar().showMessage("No data loaded for analysis")
            return
            
        analysis_type = self.analysis_selector.currentText()
        df = self.processed_data.copy()
        
        try:
            # Check for required columns
            required_columns = {'PLAYER', 'SCORE', 'CHEST', 'SOURCE'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                # Create a message about missing columns
                missing_cols_str = ", ".join(missing_columns)
                self.statusBar().showMessage(f"Missing required columns: {missing_cols_str}")
                
                # Create a simple DataFrame with a message
                result = pd.DataFrame({
                    "Message": [f"Missing required columns: {missing_cols_str}"]
                })
            else:
                # Different analysis based on the selected type
                if analysis_type == "Player Overview":
                    # Group by player and calculate various statistics
                    result = df.groupby('PLAYER').agg({
                        'SCORE': ['count', 'sum', 'mean', 'min', 'max'],
                        'CHEST': lambda x: x.value_counts().index[0] if len(x) > 0 else None,
                        'SOURCE': lambda x: x.value_counts().index[0] if len(x) > 0 else None
                    })
                    
                    # Flatten multi-index columns
                    result.columns = ['Count', 'Total Score', 'Average Score', 'Min Score', 'Max Score', 'Most Common Chest', 'Most Common Source']
                    
                    # Reset index to make Player a column
                    result = result.reset_index()
                    
                elif analysis_type == "Player Totals":
                    # Sum scores by player
                    result = df.groupby('PLAYER')['SCORE'].sum().reset_index()
                    result.columns = ['Player', 'Total Score']
                    
                elif analysis_type == "Chest Totals":
                    # Sum scores by chest type
                    result = df.groupby('CHEST')['SCORE'].sum().reset_index()
                    result.columns = ['Chest Type', 'Total Score']
                    
                elif analysis_type == "Source Totals":
                    # Sum scores by source
                    result = df.groupby('SOURCE')['SCORE'].sum().reset_index()
                    result.columns = ['Source', 'Total Score']
                    
                elif analysis_type == "Date Totals":
                    # Sum scores by date
                    if 'DATE' in df.columns:
                        # Ensure Date is datetime
                        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
                        # Group by date and sum scores
                        result = df.groupby(df['DATE'].dt.date)['SCORE'].sum().reset_index()
                        result.columns = ['Date', 'Total Score']
                    else:
                        result = pd.DataFrame(columns=['Date', 'Total Score'])
                else:
                    # Default to player overview
                    result = df.groupby('PLAYER')['SCORE'].sum().reset_index()
            
            # Update the analysis table
            model = CustomTableModel(result)
            self.analysis_view.setModel(model)
            self.analysis_view.resizeColumnsToContents()
            
            # Update status
            self.statusBar().showMessage(f"Analysis updated: {analysis_type}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Error in analysis: {str(e)}")
            log_error("Error in analysis", e, show_traceback=True)

    def filter_analysis_data(self):
        """Apply filters to the analysis data."""
        # Similar to filter_raw_data, but for the analysis table
        # Implementation would go here
        pass

    def reset_analysis_filter(self):
        """Reset all analysis filters to their default state."""
        # Reset date filter to last 30 days
        today = QDate.currentDate()
        thirty_days_ago = today.addDays(-30)
        self.analysis_start_date_edit.setDate(thirty_days_ago)
        self.analysis_end_date_edit.setDate(today)
        
        # Uncheck date filter if it's checked
        if self.analysis_date_filter_enabled.isChecked():
            self.analysis_date_filter_enabled.setChecked(False)
        
        # If value selection is visible, select all values
        if self.analysis_show_value_selection.isChecked():
            self.select_all_analysis_values()
        
        # Reprocess the data with no filters
        if self.raw_data is not None and not self.raw_data.empty:
            # Update the view with unfiltered data
            self.update_analysis_view()
        
        # Update status
        self.statusBar().showMessage("Analysis filters reset")

    def toggle_analysis_value_selection(self, state):
        """Toggle the visibility of the analysis value selection panel.
        
        Args:
            state: Can be Qt.Checked/Qt.Unchecked or a boolean True/False
        """
        # Handle different parameter types
        if isinstance(state, bool):
            is_visible = state
        elif state is None:
            # If None, use the current checkbox state
            is_visible = self.analysis_show_value_selection.isChecked()
        else:
            # Assume it's a Qt.CheckState value
            is_visible = state == Qt.Checked
        
        print(f"Toggle analysis value selection: state={state}, is_visible={is_visible}")
        
        # Set visibility
        self.analysis_value_panel.setVisible(is_visible)
        
        # Update filter options if now visible
        if is_visible:
            print("Calling update_analysis_filter_options")
            self.update_analysis_filter_options()

    def select_all_analysis_values(self):
        """Select all values in the analysis value list."""
        for i in range(self.analysis_value_list.count()):
            self.analysis_value_list.item(i).setSelected(True)

    def deselect_all_analysis_values(self):
        """Deselect all values in the analysis value list."""
        if hasattr(self, 'analysis_value_list'):
            for i in range(self.analysis_value_list.count()):
                self.analysis_value_list.item(i).setSelected(False)

    def update_chart_style(self, style):
        """Update the chart style and redraw the current chart."""
        try:
            if hasattr(self, 'mpl_canvas'):
                if style == "Default":
                    plt.style.use('dark_background')
                elif style == "Light":
                    plt.style.use('default')
                
                # Redraw the chart with the new style
                self.update_chart()
                
        except Exception as e:
            self.statusBar().showMessage(f"Error updating chart style: {str(e)}")
            log_error("Error updating chart style", e, show_traceback=True)

    def generate_report(self):
        """Generate a report based on the selected report type."""
        if self.processed_data is None or not hasattr(self, 'report_type_selector'):
            return
            
        report_type = self.report_type_selector.currentText()
        df = self.processed_data.copy()
        
        try:
            # Start with HTML header
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2A3F5F; }}
                    h2 {{ color: #45526E; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ text-align: left; padding: 8px; }}
                    th {{ background-color: #2A3F5F; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .summary {{ background-color: #EBF5FB; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <h1>Total Battle Chest Analysis Report</h1>
                <div class="summary">
                    <h2>Report Summary</h2>
                    <p>Data from: {os.path.basename(self.current_file) if hasattr(self, 'current_file') else 'Unknown'}</p>
                    <p>Report generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total records: {len(df)}</p>
                </div>
            """
            
            # Add report content based on type
            if report_type == "Player Summary" or report_type == "Full Analysis":
                html += self._generate_player_summary_html(df)
                
            if report_type == "Chest Type Analysis" or report_type == "Full Analysis":
                html += self._generate_chest_type_analysis_html(df)
                
            if report_type == "Source Analysis" or report_type == "Full Analysis":
                html += self._generate_source_analysis_html(df)
                
            if report_type == "Date Analysis" or report_type == "Full Analysis":
                html += self._generate_date_analysis_html(df)
            
            # Add charts if enabled
            if hasattr(self, 'include_charts_checkbox') and self.include_charts_checkbox.isChecked():
                html += self._generate_chart_html()
            
            # Close HTML
            html += """
            </body>
            </html>
            """
            
            # Update the report view
            self.report_view.setHtml(html)
            
            # Update status
            self.statusBar().showMessage(f"Generated report: {report_type}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Error generating report: {str(e)}")
            log_error("Error generating report", e, show_traceback=True)

    def _generate_player_summary_html(self, df):
        """Generate HTML for player summary section."""
        # Group by player and calculate statistics
        player_stats = df.groupby('Player').agg({
            'Score': ['count', 'sum', 'mean', 'min', 'max']
        })
        
        # Flatten multi-index columns
        player_stats.columns = ['Count', 'Total Score', 'Average Score', 'Min Score', 'Max Score']
        
        # Convert to HTML table
        player_table = player_stats.reset_index().to_html(index=False, classes='dataframe')
        
        # Find top players
        top_player_total = player_stats['Total Score'].idxmax()
        top_player_avg = player_stats['Average Score'].idxmax()
        
        # Create HTML section
        html = f"""
        <h2>Player Summary</h2>
        <div class="summary">
            <p>Top player by total score: <strong>{top_player_total}</strong> with {player_stats.loc[top_player_total, 'Total Score']:.0f} points</p>
            <p>Top player by average score: <strong>{top_player_avg}</strong> with {player_stats.loc[top_player_avg, 'Average Score']:.2f} points per chest</p>
        </div>
        {player_table}
        """
        
        return html

    def _generate_chest_type_analysis_html(self, df):
        """Generate HTML for chest type analysis section."""
        # Group by chest type
        chest_stats = df.groupby('ChestType').agg({
            'Score': ['count', 'sum', 'mean', 'min', 'max']
        })
        
        # Flatten multi-index columns
        chest_stats.columns = ['Count', 'Total Score', 'Average Score', 'Min Score', 'Max Score']
        
        # Convert to HTML table
        chest_table = chest_stats.reset_index().to_html(index=False, classes='dataframe')
        
        # Find best chest types
        best_chest_total = chest_stats['Total Score'].idxmax()
        best_chest_avg = chest_stats['Average Score'].idxmax()
        
        # Create HTML section
        html = f"""
        <h2>Chest Type Analysis</h2>
        <div class="summary">
            <p>Most valuable chest type (total): <strong>{best_chest_total}</strong> with {chest_stats.loc[best_chest_total, 'Total Score']:.0f} total points</p>
            <p>Most valuable chest type (average): <strong>{best_chest_avg}</strong> with {chest_stats.loc[best_chest_avg, 'Average Score']:.2f} points per chest</p>
        </div>
        {chest_table}
        """
        
        return html

    def _generate_source_analysis_html(self, df):
        """Generate HTML for source analysis section."""
        # Group by source
        source_stats = df.groupby('Source').agg({
            'Score': ['count', 'sum', 'mean', 'min', 'max']
        })
        
        # Flatten multi-index columns
        source_stats.columns = ['Count', 'Total Score', 'Average Score', 'Min Score', 'Max Score']
        
        # Convert to HTML table
        source_table = source_stats.reset_index().to_html(index=False, classes='dataframe')
        
        # Find best sources
        best_source_total = source_stats['Total Score'].idxmax()
        best_source_avg = source_stats['Average Score'].idxmax()
        
        # Create HTML section
        html = f"""
        <h2>Source Analysis</h2>
        <div class="summary">
            <p>Most valuable source (total): <strong>{best_source_total}</strong> with {source_stats.loc[best_source_total, 'Total Score']:.0f} total points</p>
            <p>Most valuable source (average): <strong>{best_source_avg}</strong> with {source_stats.loc[best_source_avg, 'Average Score']:.2f} points per chest</p>
        </div>
        {source_table}
        """
        
        return html

    def _generate_date_analysis_html(self, df):
        """Generate HTML for date analysis section."""
        # Ensure Date is datetime
        if 'Date' not in df.columns:
            return "<h2>Date Analysis</h2><p>No date data available</p>"
            
        df_with_date = df.copy()
        df_with_date['Date'] = pd.to_datetime(df_with_date['Date'], errors='coerce')
        
        # Group by date
        date_stats = df_with_date.groupby(df_with_date['Date'].dt.date).agg({
            'Score': ['count', 'sum', 'mean', 'min', 'max']
        })
        
        # Flatten multi-index columns
        date_stats.columns = ['Count', 'Total Score', 'Average Score', 'Min Score', 'Max Score']
        
        # Convert to HTML table
        date_table = date_stats.reset_index().to_html(index=False, classes='dataframe')
        
        # Find best dates
        best_date_total = date_stats['Total Score'].idxmax()
        best_date_avg = date_stats['Average Score'].idxmax()
        
        # Create HTML section
        html = f"""
        <h2>Date Analysis</h2>
        <div class="summary">
            <p>Best date by total score: <strong>{best_date_total}</strong> with {date_stats.loc[best_date_total, 'Total Score']:.0f} points</p>
            <p>Best date by average score: <strong>{best_date_avg}</strong> with {date_stats.loc[best_date_avg, 'Average Score']:.2f} points per chest</p>
        </div>
        {date_table}
        """
        
        return html

    def _generate_chart_html(self):
        """Generate HTML with embedded chart image."""
        # Save current chart to a temporary file
        temp_file = os.path.join(self.temp_dir, "temp_chart.png")
        self.mpl_canvas.figure.savefig(temp_file, dpi=100, bbox_inches='tight')
        
        # Create HTML section with the image
        html = f"""
        <h2>Chart Visualization</h2>
        <div>
            <img src="file:///{temp_file.replace(os.sep, '/')}" style="max-width: 100%; height: auto;" />
        </div>
        """
        
        return html
        
    def export_raw_data(self):
        """Export the raw data (filtered or unfiltered) to a CSV file."""
        if self.processed_data is None or self.processed_data.empty:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
            
        # Get the model from the table view
        model = self.raw_data_table.model()
        if model is None:
            # If no filtered model, use the full processed data
            data_to_export = self.processed_data
        else:
            # Get data from the current model
            rows = model.rowCount()
            cols = model.columnCount()
            
            if rows == 0 or cols == 0:
                QMessageBox.warning(self, "Warning", "No data to export")
                return
                
            # Use the raw data model to access the data
            data_to_export = model._data.copy()
            
        # Ask for file location
        file_path, filter = QFileDialog.getSaveFileName(
            self,
            "Export Data to CSV",
            str(self.export_dir / "export.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:  # User canceled
            return
            
        try:
            # Export with UTF-8 encoding to preserve umlauts
            data_to_export.to_csv(file_path, index=False, encoding='utf-8')
            
            # Update status
            self.statusBar().showMessage(f"Exported {len(data_to_export)} records to {os.path.basename(file_path)}")
            
            # Ask if user wants to open the file
            reply = QMessageBox.question(
                self,
                "Export Complete",
                "Data exported successfully. Would you like to open the file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Open the file with default application
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
                    
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting file: {str(e)}")
            log_error("Error exporting CSV file", e, show_traceback=True)
            
            # Show error message
            error_msg = QMessageBox(self)
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setWindowTitle("Error Exporting File")
            error_msg.setText(f"Error exporting file: {str(e)}")
            error_msg.setDetailedText(traceback.format_exc())
            error_msg.exec_()

    def export_analysis_data(self):
        """Export the analysis data to a CSV file."""
        if self.analysis_view.model() is None:
            self.statusBar().showMessage("No analysis data to export")
            return
            
        # Get data from the model
        model = self.analysis_view.model()
        df = model.dataframe
        
        # Ask for file name
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Data",
            str(self.export_dir),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:  # User canceled
            return
            
        try:
            # Export to CSV
            df.to_csv(file_path, index=False)
            self.statusBar().showMessage(f"Analysis data exported to {file_path}")
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting analysis data: {str(e)}")
            log_error("Error exporting analysis data", e, show_traceback=True)

    def export_chart(self):
        """Export the current chart to an image file."""
        if not hasattr(self, 'mpl_canvas'):
            self.statusBar().showMessage("No chart to export")
            return
            
        # Ask for file name
        file_path, filter = QFileDialog.getSaveFileName(
            self,
            "Export Chart",
            str(self.export_dir),
            "PNG Files (*.png);;JPEG Files (*.jpg);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)"
        )
        
        if not file_path:  # User canceled
            return
            
        try:
            # Export chart to the selected format
            self.mpl_canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            self.statusBar().showMessage(f"Chart exported to {file_path}")
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting chart: {str(e)}")
            log_error("Error exporting chart", e, show_traceback=True)

    def export_report(self):
        """Export the current report to an HTML file."""
        if not hasattr(self, 'report_view') or self.report_view.toHtml() == "":
            self.statusBar().showMessage("No report to export")
            return
            
        # Ask for file name
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            str(self.export_dir),
            "HTML Files (*.html);;All Files (*)"
        )
        
        if not file_path:  # User canceled
            return
            
        try:
            # Export report HTML
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.report_view.toHtml())
                
            self.statusBar().showMessage(f"Report exported to {file_path}")
        except Exception as e:
            self.statusBar().showMessage(f"Error exporting report: {str(e)}")
            log_error("Error exporting report", e, show_traceback=True)

    def print_report(self):
        """Print the current report."""
        from PySide6.QtPrintSupport import QPrintDialog
        
        if not hasattr(self, 'report_view') or self.report_view.toHtml() == "":
            self.statusBar().showMessage("No report to print")
            return
            
        try:
            # Create printer
            printer = QPrinter(QPrinter.HighResolution)
            # Use A4 size (don't use QPageSize which might not be available)
            printer.setPageSize(QPrinter.A4)
            printer.setColorMode(QPrinter.Color)
            
            # Show print dialog
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                # Print the report
                self.report_view.print_(printer)
                self.statusBar().showMessage("Report sent to printer")
        except Exception as e:
            self.statusBar().showMessage(f"Error printing report: {str(e)}")
            log_error("Error printing report", e, show_traceback=True)

    def show_preferences(self):
        """Show the preferences dialog."""
        # Implement preferences dialog
        QMessageBox.information(
            self,
            "Preferences",
            "Preferences dialog not implemented yet."
        )

    def set_theme(self, theme_name):
        """Set the application theme."""
        if theme_name == "dark":
            # Apply dark theme
            self.config_manager.set_theme("dark")
            self.style_manager.apply_dark_theme()
        else:
            # Apply light theme
            self.config_manager.set_theme("light")
            self.style_manager.apply_light_theme()
            
        # Update the chart style if we have a chart
        if hasattr(self, 'chart_type_combo'):
            self.update_chart_style("Default" if theme_name == "dark" else "Light")
        
        # Update status
        self.statusBar().showMessage(f"Applied {theme_name} theme")

    def show_about_dialog(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Total Battle Analyzer",
            """<h1>Total Battle Analyzer</h1>
            <p>Version 1.0.0</p>
            <p>A tool for analyzing chest data from Total Battle game.</p>
            <p>Copyright © 2023</p>"""
        )

    def show_help(self):
        """Show the help documentation."""
        QMessageBox.information(
            self,
            "Help",
            """<h1>Total Battle Analyzer Help</h1>
            <h2>Quick Start</h2>
            <p>1. Import your CSV data by dragging and dropping a file or using the file selector.</p>
            <p>2. View and filter your raw data in the Raw Data tab.</p>
            <p>3. Explore different analyses in the Analysis tab.</p>
            <p>4. Visualize your data with charts in the Charts tab.</p>
            <p>5. Generate comprehensive reports in the Reports tab.</p>"""
        )

    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        if not hasattr(self, 'recent_files_menu'):
            return
            
        self.recent_files_menu.clear()
        
        recent_files = self.config_manager.get_recent_files()
        
        for file_path in recent_files:
            action = self.recent_files_menu.addAction(os.path.basename(file_path))
            action.setData(file_path)
            action.triggered.connect(lambda checked, path=file_path: self.load_csv_file(path))

    def _populate_recent_files_list(self):
        """Populate the recent files list in the import tab."""
        if not hasattr(self, 'recent_files_list'):
            return
            
        self.recent_files_list.clear()
        
        recent_files = self.config_manager.get_recent_files()
        
        for file_path in recent_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)
            self.recent_files_list.addItem(item)

    def _on_recent_file_clicked(self, item):
        """Handle click on a recent file in the list."""
        file_path = item.data(Qt.UserRole)
        self.load_csv_file(file_path)

    def select_all_values(self):
        """Select all values in the value list."""
        if hasattr(self, 'value_list'):
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(True)
            
    def deselect_all_values(self):
        """Deselect all values in the value list."""
        if hasattr(self, 'value_list'):
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(False)
            
    def update_filter_from_selection(self):
        """Update the filter based on the selected values in the value list."""
        # Implement the filtering logic based on selected values
        pass
        
    def filter_analysis_data(self):
        """Apply filters to the analysis data."""
        # Similar to filter_raw_data, but for the analysis table
        pass

    def reset_analysis_filter(self):
        """Reset analysis filters."""
        # Reset date filter to last 30 days
        today = QDate.currentDate()
        thirty_days_ago = today.addDays(-30)
        self.analysis_start_date_edit.setDate(thirty_days_ago)
        self.analysis_end_date_edit.setDate(today)
        
        # Uncheck date filter if it's checked
        if self.analysis_date_filter_enabled.isChecked():
            self.analysis_date_filter_enabled.setChecked(False)
        
        # If value selection is visible, select all values
        if self.analysis_show_value_selection.isChecked():
            self.select_all_analysis_values()
        
        # Reprocess the data with no filters
        if self.raw_data is not None and not self.raw_data.empty:
            # Update the view with unfiltered data
            self.update_analysis_view()
        
        # Update status
        self.statusBar().showMessage("Analysis filters reset")

    def select_all_analysis_values(self):
        """Select all values in the analysis value list."""
        if hasattr(self, 'analysis_value_list'):
            for i in range(self.analysis_value_list.count()):
                self.analysis_value_list.item(i).setSelected(True)

    def deselect_all_analysis_values(self):
        """Deselect all values in the analysis value list."""
        if hasattr(self, 'analysis_value_list'):
            for i in range(self.analysis_value_list.count()):
                self.analysis_value_list.item(i).setSelected(False)
                
    def update_chart_style(self, style):
        """Update the chart style and redraw the current chart."""
        try:
            if hasattr(self, 'mpl_canvas'):
                if style == "Default":
                    plt.style.use('dark_background')
                elif style == "Light":
                    plt.style.use('default')
                
                # Redraw the chart with the new style
                self.update_chart()
                
        except Exception as e:
            self.statusBar().showMessage(f"Error updating chart style: {str(e)}")
            log_error("Error updating chart style", e, show_traceback=True)

    def update_analysis_filter_options(self):
        """
        Update the analysis filter options based on the selected column.
        
        This method clears the analysis value list and populates it with
        unique values from the selected column. It also updates the analysis
        view based on the selected options.
        """
        if self.debug:
            print("Updating analysis filter options...")
        
        # Get the selected column
        column = self.analysis_column_selector.currentText()
        if not column or self.raw_data is None:
            return
        
        # Clear the analysis value list
        self.analysis_value_list.clear()
        if self.debug:
            print(f"Cleared analysis_value_list")
        
        # Get unique values from the selected column
        unique_values = self.raw_data[column].unique()
        if self.debug:
            print(f"Selected column: {column}")
            print(f"Found {len(unique_values)} unique values")
        
        # Add the unique values to the analysis value list
        for value in unique_values:
            self.analysis_value_list.addItem(str(value))
        
        if self.debug:
            print(f"Added {len(unique_values)} unique values to analysis_value_list")
        
        # Update the analysis view
        self.update_analysis_view()

    def _setup_ui(self):
        """Set up the UI components with proper styling"""
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create main tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # Cleaner look
        
        # Create import tab
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_layout.setContentsMargins(10, 10, 10, 10)
        import_layout.setSpacing(10)
        
        # Add file label
        self.file_label = QLabel("No file loaded")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet(f"""
            QLabel {{
                color: {DARK_THEME['text_disabled']};
                font-size: 14px;
                padding: 10px;
            }}
        """)
        import_layout.addWidget(self.file_label)
        
        # Create drop area and import area
        self.drop_area = DropArea(self)
        self.import_area = ImportArea(self)
        
        # Add to import layout
        import_layout.addWidget(self.drop_area)
        import_layout.addWidget(self.import_area)
        import_layout.addStretch()
        
        # Create raw data tab with splitter
        raw_data_tab = QWidget()
        raw_data_layout = QVBoxLayout(raw_data_tab)
        raw_data_layout.setContentsMargins(10, 10, 10, 10)
        raw_data_layout.setSpacing(10)
        
        # Create horizontal splitter for filter area and table
        raw_data_splitter = QSplitter(Qt.Horizontal)
        
        # Create left panel for filter controls (instead of using filter_area)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        # Create filter controls group
        filter_group = QGroupBox("Filter and View Options")
        filter_layout = QVBoxLayout()
        
        # Column selection
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("Filter Column:"))
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_filter_options)
        column_layout.addWidget(self.column_selector)
        filter_layout.addLayout(column_layout)
        
        # Value selection toggle
        self.show_value_selection = QCheckBox("Select specific values")
        self.show_value_selection.setChecked(True)
        self.show_value_selection.stateChanged.connect(self.toggle_value_selection)
        filter_layout.addWidget(self.show_value_selection)
        
        # Value selection area
        self.value_list_widget = QWidget()
        value_list_layout = QVBoxLayout(self.value_list_widget)
        value_list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Value list with multiple selection
        self.value_list = QListWidget()
        self.value_list.setSelectionMode(QAbstractItemView.MultiSelection)
        value_list_layout.addWidget(self.value_list)
        
        # Value selection buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_values)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_values)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        value_list_layout.addLayout(button_layout)
        
        # Add value selection to filter layout
        filter_layout.addWidget(self.value_list_widget)
        
        # Date filter section
        date_group = QGroupBox("Date Filter")
        date_layout = QVBoxLayout()
        
        self.date_filter_enabled = QCheckBox("Enable Date Filter")
        date_layout.addWidget(self.date_filter_enabled)
        
        date_range_layout = QGridLayout()
        date_range_layout.addWidget(QLabel("From:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        date_range_layout.addWidget(self.start_date_edit, 0, 1)
        
        date_range_layout.addWidget(QLabel("To:"), 1, 0)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.end_date_edit, 1, 1)
        
        date_layout.addLayout(date_range_layout)
        date_group.setLayout(date_layout)
        filter_layout.addWidget(date_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        apply_button = QPushButton("Apply Filter")
        apply_button.clicked.connect(self.filter_raw_data)
        clear_button = QPushButton("Clear Filter")
        clear_button.clicked.connect(self.clear_filters)
        action_layout.addWidget(apply_button)
        action_layout.addWidget(clear_button)
        filter_layout.addLayout(action_layout)
        
        # Set filter group layout
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        left_layout.addStretch()
        
        # Add left panel to splitter
        raw_data_splitter.addWidget(left_panel)
        
        # Create table view for raw data
        self.raw_data_table = QTableView()
        self.raw_data_table.setSortingEnabled(True)
        self.raw_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.raw_data_table.horizontalHeader().setMinimumSectionSize(80)
        self.raw_data_table.setAlternatingRowColors(True)
        raw_data_splitter.addWidget(self.raw_data_table)
        
        # Set splitter sizes (30% filter area, 70% table)
        raw_data_splitter.setSizes([300, 700])
        raw_data_layout.addWidget(raw_data_splitter)
        
        # Create analysis tab with splitter
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        analysis_layout.setContentsMargins(10, 10, 10, 10)
        analysis_layout.setSpacing(10)
        
        # Create horizontal splitter for analysis controls and table
        analysis_splitter = QSplitter(Qt.Horizontal)
        self.analysis_splitter = analysis_splitter  # Store reference for later use
        
        # Create left panel for analysis controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Filter controls
        filter_group = QGroupBox("Filter and View Options")
        filter_layout = QVBoxLayout()
        
        # Analysis view selector
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("View:"))
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems([
            "Player Overview",
            "Player Totals",
            "Chest Totals",
            "Source Totals",
            "Date Totals"
        ])
        self.analysis_selector.currentIndexChanged.connect(self.update_analysis_view)
        view_layout.addWidget(self.analysis_selector)
        filter_layout.addLayout(view_layout)
        
        # Column selector
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("Filter Column:"))
        self.analysis_column_selector = QComboBox()
        self.analysis_column_selector.currentIndexChanged.connect(self.update_analysis_filter_options)
        column_layout.addWidget(self.analysis_column_selector)
        filter_layout.addLayout(column_layout)
        
        # Value selection
        self.analysis_show_value_selection = QCheckBox("Select specific values")
        self.analysis_show_value_selection.setChecked(True)
        self.analysis_show_value_selection.stateChanged.connect(self.toggle_analysis_value_selection)
        filter_layout.addWidget(self.analysis_show_value_selection)
        
        # Create value list widget
        self.analysis_value_panel = QWidget()
        value_panel_layout = QVBoxLayout(self.analysis_value_panel)
        value_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Value list
        self.analysis_value_list = QListWidget()
        self.analysis_value_list.setSelectionMode(QAbstractItemView.MultiSelection)
        value_panel_layout.addWidget(self.analysis_value_list)
        
        # Select/Deselect buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_analysis_values)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_analysis_values)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        value_panel_layout.addLayout(button_layout)
        
        # Add value panel to filter layout
        filter_layout.addWidget(self.analysis_value_panel)
        
        # Date filter
        date_group = QGroupBox("Date Filter")
        date_layout = QVBoxLayout()
        
        self.analysis_date_filter_enabled = QCheckBox("Enable date filter")
        date_layout.addWidget(self.analysis_date_filter_enabled)
        
        date_range_layout = QGridLayout()
        date_range_layout.addWidget(QLabel("From:"), 0, 0)
        self.analysis_start_date_edit = QDateEdit()
        self.analysis_start_date_edit.setCalendarPopup(True)
        self.analysis_start_date_edit.setDate(QDate.currentDate().addDays(-30))
        date_range_layout.addWidget(self.analysis_start_date_edit, 0, 1)
        
        date_range_layout.addWidget(QLabel("To:"), 1, 0)
        self.analysis_end_date_edit = QDateEdit()
        self.analysis_end_date_edit.setCalendarPopup(True)
        self.analysis_end_date_edit.setDate(QDate.currentDate())
        date_range_layout.addWidget(self.analysis_end_date_edit, 1, 1)
        
        date_layout.addLayout(date_range_layout)
        date_group.setLayout(date_layout)
        filter_layout.addWidget(date_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self.filter_analysis_data)
        clear_filter_btn = QPushButton("Clear Filter")
        clear_filter_btn.clicked.connect(self.reset_analysis_filter)
        action_layout.addWidget(apply_filter_btn)
        action_layout.addWidget(clear_filter_btn)
        filter_layout.addLayout(action_layout)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        left_layout.addStretch()
        
        # Add left panel to splitter
        analysis_splitter.addWidget(left_panel)
        
        # Create analysis table
        self.analysis_view = QTableView()
        self.analysis_view.setSortingEnabled(True)
        self.analysis_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.analysis_view.horizontalHeader().setMinimumSectionSize(100)
        self.analysis_view.setAlternatingRowColors(True)
        analysis_splitter.addWidget(self.analysis_view)
        
        # Set splitter sizes (30% controls, 70% table)
        analysis_splitter.setSizes([300, 700])
        analysis_layout.addWidget(analysis_splitter)
        
        # Create charts tab
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)
        charts_layout.setContentsMargins(10, 10, 10, 10)
        charts_layout.setSpacing(10)
        
        # Create chart controls
        chart_controls = QHBoxLayout()
        chart_type_label = QLabel("Chart Type:")
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Player Totals",
            "Chest Totals",
            "Source Totals",
            "Date Totals"
        ])
        self.chart_type_combo.currentIndexChanged.connect(self.update_chart)
        chart_controls.addWidget(chart_type_label)
        chart_controls.addWidget(self.chart_type_combo)
        chart_controls.addStretch()
        
        # Create matplotlib canvas
        self.mpl_canvas = MplCanvas(width=10, height=6, dpi=100)
        
        # Add widgets to chart layout
        charts_layout.addLayout(chart_controls)
        charts_layout.addWidget(self.mpl_canvas)
        
        # Add tabs to tab widget
        self.tabs.addTab(import_tab, "Import")
        self.tabs.addTab(raw_data_tab, "Raw Data")
        self.tabs.addTab(analysis_tab, "Analysis")
        self.tabs.addTab(charts_tab, "Charts")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)
        
        # Set central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Set window properties
        self.setWindowTitle(self.title)
        self.resize(1200, 800)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_chart)
        self.refresh_timer.start(5000)  # Update every 5 seconds

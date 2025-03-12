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
from datetime import datetime
from pathlib import Path
import re

# Data manipulation and visualization
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

# Qt imports
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QTableView, QTabWidget, QSplitter, QFrame,
    QComboBox, QLineEdit, QGroupBox, QCheckBox, QListWidget, QHeaderView,
    QAbstractItemView, QDateEdit, QTextBrowser, QApplication,
    QListWidgetItem, QStatusBar, QGridLayout, QSizePolicy, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QDate, QSettings, QDir, Signal, QSortFilterProxyModel
from PySide6.QtGui import QIcon, QColor
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6 import QtUiTools

# Import custom modules
from .utils import log_error
from .stylemanager import StyleManager, DARK_THEME
from .configmanager import ConfigManager
from .customtablemodel import CustomTableModel
from .mplcanvas import MplCanvas
from .importarea import ImportArea
from .dataprocessor import DataProcessor
from .filterarea import FilterArea

class MainWindow(QMainWindow):
    """
    Main window of the Total Battle Analyzer application.
    Provides functionality for importing, filtering, and visualizing chest data.
    """
    
    def __init__(self, title="Total Battle Analyzer", debug=True):
        """
        Initialize the main window.
        
        Args:
            title (str, optional): Window title. Defaults to "Total Battle Analyzer".
            debug (bool, optional): Enable debug output. Defaults to True.
        """
        super().__init__()
        
        # Set debug mode
        self.debug = debug
        
        # Initialize data attributes
        self.raw_data = None
        self.processed_data = None
        self.analysis_data = None
        
        # Initialize visibility tracking variables
        self._was_value_list_visible = False
        self._was_analysis_value_panel_visible = False
        
        # Initialize configuration
        self.config_manager = ConfigManager(title)
        
        # Set window title
        self.setWindowTitle(title)
        
        # Set up directories
        self.import_dir = Path(self.config_manager.get_import_directory())
        self.export_dir = Path(self.config_manager.get_export_directory())
        
        # Create directories if they don't exist
        os.makedirs(self.import_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Set window size from config
        width, height = self.config_manager.get_window_size()
        self.resize(width, height)
        
        # Setup UI components
        self.setup_ui_components()
        
        # Initialize tab states
        self.init_tab_states()
        
        # Apply dark theme
        self.apply_theme()
        
        # Connect signals to slots
        self.connect_signals()
        
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
        """Initialize tab states."""
        # Initialize Raw Data tab
        if hasattr(self, 'column_selector'):
            self.column_selector.clear()
            
        # Call toggle methods instead of setting visibility directly
        if hasattr(self, 'show_value_selection') and hasattr(self, 'value_list_widget'):
            # Force the checkbox state to trigger the toggle method
            if self.debug:
                print(f"Raw data tab - initializing with show_value_selection checked: {self.show_value_selection.isChecked()}")
            self.toggle_value_selection()
            
        # Initialize Analysis tab
        if hasattr(self, 'analysis_column_selector'):
            self.analysis_column_selector.clear()
            
        # Call toggle methods for analysis tab instead of setting visibility directly
        if hasattr(self, 'analysis_show_value_selection') and hasattr(self, 'analysis_value_panel'):
            if self.debug:
                print(f"Analysis tab - initializing with analysis_show_value_selection checked: {self.analysis_show_value_selection.isChecked()}")
            self.toggle_analysis_value_selection()
        
        # Set status message
        self.statusBar().showMessage("Ready")

    def load_csv_file(self, file_path):
        """
        Load a CSV file and process the data.
        
        Args:
            file_path (str): Path to the CSV file to load
        """
        if self.debug:
            print(f"\n--- LOAD CSV FILE: {file_path} ---\n")
        
        try:
            # Detect encoding
            encodings_to_try = ['utf-8', 'latin1', 'cp1252']
            
            # Try to detect encoding based on content
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)  # Read first 1KB to detect encoding
                
                # Check for UTF-8 BOM
                if raw_data.startswith(b'\xef\xbb\xbf'):
                    detected_encoding = 'utf-8-sig'
                    if self.debug:
                        print("Detected UTF-8 with BOM")
                # Check for UTF-8 pattern (look for German umlauts)
                elif b'\xc3\xa4' in raw_data or b'\xc3\xb6' in raw_data or b'\xc3\xbc' in raw_data:
                    detected_encoding = 'utf-8'
                    if self.debug:
                        print("Detected UTF-8 encoding based on umlaut pattern")
                        print(f"Raw data sample: {raw_data}")
                else:
                    # Default to UTF-8 but will try others if it fails
                    detected_encoding = 'utf-8'
                
                if self.debug:
                    print(f"Detected encoding: {detected_encoding} based on content analysis")
                    print(f"Trying detected encoding first: {detected_encoding}")
            
            # Try the detected encoding first, then fall back to others
            if detected_encoding in encodings_to_try:
                encodings_to_try.remove(detected_encoding)
            encodings_to_try.insert(0, detected_encoding)
            
            # Try each encoding until one works
            for encoding in encodings_to_try:
                try:
                    if self.debug:
                        print(f"Trying encoding: {encoding}")
                    
                    self.raw_data = pd.read_csv(file_path, encoding=encoding)
                    
                    # Check if we can read player names with umlauts
                    if 'PLAYER' in self.raw_data.columns:
                        if self.debug:
                            print(f"Sample players with {encoding}: {self.raw_data['PLAYER'].head().tolist()}")
                        
                        # Check for umlauts in player names
                        for player in self.raw_data['PLAYER'].head():
                            if 'ä' in str(player) or 'ö' in str(player) or 'ü' in str(player) or 'ß' in str(player):
                                if self.debug:
                                    print(f"Found umlauts in player name: {player}")
                    
                    break  # Successfully loaded
                except UnicodeDecodeError:
                    if self.debug:
                        print(f"Failed with encoding: {encoding}")
                    continue
            
            # Check if we have required columns
            required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
            
            # Rename columns to standardized names if needed (case-insensitive)
            column_mapping = {
                'date': 'DATE',
                'player': 'PLAYER',
                'source': 'SOURCE',
                'chest': 'CHEST',
                'score': 'SCORE',
                'clan': 'CLAN'
            }
            
            self.raw_data.rename(columns=lambda x: column_mapping.get(x.lower(), x), inplace=True)
            
            # Convert SCORE to numeric
            if 'SCORE' in self.raw_data.columns:
                self.raw_data['SCORE'] = pd.to_numeric(self.raw_data['SCORE'], errors='coerce')
            
            # Convert DATE to datetime
            if 'DATE' in self.raw_data.columns:
                self.raw_data['DATE'] = pd.to_datetime(self.raw_data['DATE'], errors='coerce')
            
            # Set processed data to raw data initially
            self.processed_data = self.raw_data.copy()
            self.analysis_data = self.raw_data.copy()
            
            if self.debug:
                print("\n--- UI COMPONENT UPDATES ---\n")
                print(f"Raw data columns: {self.raw_data.columns.tolist()}")
                print(f"Raw data shape: {self.raw_data.shape}")
            
            # Update UI components
            if self.debug:
                print("\n--- UPDATING RAW DATA TAB ---\n")
            
            # Update column selector in the Raw Data tab
            self.column_selector.clear()
            self.column_selector.addItems(self.raw_data.columns.tolist())
            
            if self.debug:
                print(f"Populating column_selector with columns: {self.raw_data.columns.tolist()}\n")
            
            # Update filter options
            self.update_filter_options()
            
            # Create and set table model
            self._create_raw_data_model()
            
            # Update analysis tab
            if self.debug:
                print("\n--- UPDATING ANALYSIS TAB ---\n")
            
            # Update column selector in the Analysis tab
            self.analysis_column_selector.clear()
            self.analysis_column_selector.addItems(self.raw_data.columns.tolist())
            
            if self.debug:
                print(f"Populating analysis_column_selector with columns: {self.raw_data.columns.tolist()}")
            
            # Update analysis filter options
            self.update_analysis_filter_options()
            
            # Update analysis view
            self.update_analysis_view()
            
            # Update chart
            self.update_chart()
            
            # Update filter panel visibility
            if self.debug:
                print("\n--- UPDATING FILTER PANEL VISIBILITY ---\n")
            
            # Ensure Raw Data tab value list visibility matches checkbox
            if hasattr(self, 'show_value_selection') and hasattr(self, 'value_list_widget'):
                self.toggle_value_selection()
            
            # Ensure Analysis tab value list visibility matches checkbox
            if hasattr(self, 'analysis_show_value_selection') and hasattr(self, 'analysis_value_panel'):
                self.toggle_analysis_value_selection()
            
            # Update file label
            self.file_label.setText(f"Loaded: {os.path.basename(file_path)}")
            
            if self.debug:
                print(f"\n--- COMPLETED LOADING FILE: {file_path} ---\n")
            
            return True
        except Exception as e:
            if self.debug:
                print(f"Error loading CSV file: {str(e)}")
            self.show_error_dialog("Error Loading File", f"Could not load the CSV file: {str(e)}")
            return False

    def apply_filter(self):
        """Apply the filter to the raw data."""
        if self.raw_data is None:
            return
        
        # Get selected column
        column = self.column_selector.currentText()
        if not column:
            return
        
        # Get selected values
        selected_values = []
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            if item.isSelected():
                selected_values.append(item.text())
        
        # Apply filter
        if selected_values:
            self.processed_data = self.raw_data[self.raw_data[column].astype(str).isin(selected_values)]
            self.statusBar().showMessage(f"Filtered by {column}: {len(selected_values)} values selected")
        else:
            self.processed_data = self.raw_data.copy()
            self.statusBar().showMessage("No filter applied")
        
        # Update table
        self.update_raw_data_table()

    def reset_filter(self):
        """Reset the filter and show all data."""
        if self.raw_data is None:
            return
        
        # Reset processed data to raw data
        self.processed_data = self.raw_data.copy()
        
        # Select all values in the value list
        self.select_all_values()
        
        # Update table
        self.update_raw_data_table()
        
        self.statusBar().showMessage("Filter reset")

    def apply_analysis_filter(self):
        """Apply the filter to the analysis data."""
        if self.raw_data is None:
            return
        
        # Get selected column
        column = self.analysis_column_selector.currentText()
        if not column:
            return
        
        # Get selected values
        selected_values = []
        for i in range(self.analysis_value_list.count()):
            item = self.analysis_value_list.item(i)
            if item.isSelected():
                selected_values.append(item.text())
        
        # Apply filter
        if selected_values:
            self.analysis_data = self.raw_data[self.raw_data[column].astype(str).isin(selected_values)]
            self.statusBar().showMessage(f"Analysis filtered by {column}: {len(selected_values)} values selected")
        else:
            self.analysis_data = self.raw_data.copy()
            self.statusBar().showMessage("No analysis filter applied")
        
        # Update analysis view
        self.update_analysis_view()
        
        # Update chart to reflect the filtered data
        self.update_chart()

    def reset_analysis_filter(self):
        """Reset all analysis filters to their default state."""
        if self.raw_data is None:
            return
        
        # Reset analysis data to raw data
        self.analysis_data = self.raw_data.copy()
            
        # Reset date filter to last 30 days
        if hasattr(self, 'analysis_start_date_edit') and hasattr(self, 'analysis_end_date_edit'):
            today = QDate.currentDate()
            thirty_days_ago = today.addDays(-30)
            self.analysis_start_date_edit.setDate(thirty_days_ago)
            self.analysis_end_date_edit.setDate(today)
            
            # Uncheck date filter if it's checked
            if hasattr(self, 'analysis_date_filter_enabled') and self.analysis_date_filter_enabled.isChecked():
                self.analysis_date_filter_enabled.setChecked(False)
        
        # If value selection is visible, select all values
        if hasattr(self, 'analysis_show_value_selection') and self.analysis_show_value_selection.isChecked():
            self.select_all_analysis_values()
        
        # Update the view with unfiltered data
        self.update_analysis_view()
        
        # Update chart to reflect the reset data
        self.update_chart()
        
        # Update status
        self.statusBar().showMessage("Analysis filters reset")

    def update_chart(self):
        """Update the chart based on the selected chart type and options."""
        if self.debug:
            print(f"Update chart called")
        
        # Check if we have a chart selector and canvas
        if not hasattr(self, 'analysis_chart_selector') or not hasattr(self, 'chart_canvas'):
            if self.debug:
                print("Chart selector or canvas not found")
            return
            
        # Check if we have analysis results
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            if self.debug:
                print("No analysis results available for charting")
            return
        
        try:
            # Get the selected chart type and options
            chart_type = self.analysis_chart_selector.currentText()
            
            # Get selected data column
            data_column = self.chart_data_column.currentText() if hasattr(self, 'chart_data_column') else "SCORE"
            
            # Get sort options
            sort_column = self.chart_sort_column.currentText() if hasattr(self, 'chart_sort_column') else data_column
            sort_ascending = self.chart_sort_order.currentText() == "Ascending" if hasattr(self, 'chart_sort_order') else False
            
            # Get limit options
            limit_results = self.chart_limit_checkbox.isChecked() if hasattr(self, 'chart_limit_checkbox') else False
            limit_value = self.chart_limit_value.value() if hasattr(self, 'chart_limit_value') else 10
            
            # Get display options
            show_values = self.chart_show_values.isChecked() if hasattr(self, 'chart_show_values') else True
            show_grid = self.chart_show_grid.isChecked() if hasattr(self, 'chart_show_grid') else True
            
            # Clear the figure
            self.chart_figure.clear()
            
            # Set the chart background color to match application theme
            self.chart_figure.patch.set_facecolor('#1A2742')
            
            # Create subplot
            ax = self.chart_figure.add_subplot(111)
            ax.set_facecolor('#1A2742')
            
            # Set grid visibility based on option
            if show_grid:
                ax.grid(True, color='#3A4762', linestyle='-', linewidth=0.5, alpha=0.7)
            else:
                ax.grid(False)
            
            # Set text colors
            ax.xaxis.label.set_color('#FFFFFF')
            ax.yaxis.label.set_color('#FFFFFF')
            ax.title.set_color('#D4AF37')
            for text in ax.get_xticklabels() + ax.get_yticklabels():
                text.set_color('#FFFFFF')
            
            # Get data based on chart type
            if chart_type == "Player Totals":
                data = self.analysis_results['player_totals'].copy()
                if len(data) > 0:
                    # Make sure the data column exists
                    if data_column not in data.columns:
                        data_column = "SCORE"  # Fallback to SCORE if column doesn't exist
                    
                    # Sort data
                    if sort_column in data.columns:
                        data = data.sort_values(sort_column, ascending=sort_ascending)
                    
                    # Limit results if needed
                    if limit_results and len(data) > limit_value:
                        if sort_ascending:
                            data = data.head(limit_value)  # Keep first N rows if ascending
                        else:
                            data = data.tail(limit_value)  # Keep last N rows if descending
                    
                    # Create horizontal bar chart
                    bars = ax.barh(data['PLAYER'].values, data[data_column].values, color='#D4AF37')
                    ax.set_xlabel(f'{data_column.replace("_", " ").title()}')
                    ax.set_title(f'Player {data_column.replace("_", " ").title()}')
                    
                    # Add values at the end of each bar if requested
                    if show_values:
                        for i, bar in enumerate(bars):
                            value = data[data_column].values[i]
                            ax.text(value, bar.get_y() + bar.get_height()/2, f" {value:,.0f}", 
                                   va='center', color='white', fontweight='bold')
                
            elif chart_type == "Chest Totals":
                data = self.analysis_results['chest_totals'].copy()
                if len(data) > 0:
                    # Make sure the data column exists
                    if data_column not in data.columns:
                        data_column = "SCORE"  # Fallback to SCORE if column doesn't exist
                    
                    # Sort data
                    if sort_column in data.columns:
                        data = data.sort_values(sort_column, ascending=sort_ascending)
                    
                    # Limit results if needed
                    if limit_results and len(data) > limit_value:
                        if sort_ascending:
                            data = data.head(limit_value)  # Keep first N rows if ascending
                        else:
                            data = data.tail(limit_value)  # Keep last N rows if descending
                    
                    # Create bar chart
                    bars = ax.bar(data['CHEST'].values, data[data_column].values, color='#5991C4')
                    ax.set_ylabel(f'{data_column.replace("_", " ").title()}')
                    ax.set_title(f'Chest Type {data_column.replace("_", " ").title()}')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                    
                    # Add values on top of each bar if requested
                    if show_values:
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                
            elif chart_type == "Source Totals":
                data = self.analysis_results['source_totals'].copy()
                if len(data) > 0:
                    # Make sure the data column exists
                    if data_column not in data.columns:
                        data_column = "SCORE"  # Fallback to SCORE if column doesn't exist
                    
                    # Sort data
                    if sort_column in data.columns:
                        data = data.sort_values(sort_column, ascending=sort_ascending)
                    
                    # Limit results if needed
                    if limit_results and len(data) > limit_value:
                        if sort_ascending:
                            data = data.head(limit_value)  # Keep first N rows if ascending
                        else:
                            data = data.tail(limit_value)  # Keep last N rows if descending
                    
                    # Create pie chart
                    pie_colors = ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F', '#9966CC', '#F0C75A', '#527A96']
                    wedges, texts, autotexts = ax.pie(
                        data[data_column].values, 
                        labels=data['SOURCE'].values, 
                        autopct='%1.1f%%' if show_values else '',
                        colors=pie_colors[:len(data)],
                        startangle=90,
                        wedgeprops={'edgecolor': '#1A2742', 'linewidth': 1}
                    )
                    for text in texts + autotexts:
                        text.set_color('white')
                    for autotext in autotexts:
                        autotext.set_fontweight('bold')
                    ax.set_title(f'Distribution by Source ({data_column.replace("_", " ").title()})')
                
            elif chart_type == "Date Totals":
                data = self.analysis_results['date_totals'].copy()
                if len(data) > 0:
                    # Make sure the data column exists
                    if data_column not in data.columns:
                        data_column = "SCORE"  # Fallback to SCORE if column doesn't exist
                    
                    # Sort data
                    if sort_column in data.columns:
                        data = data.sort_values(sort_column, ascending=sort_ascending)
                    
                    # Limit results if needed
                    if limit_results and len(data) > limit_value:
                        if sort_ascending:
                            data = data.head(limit_value)  # Keep first N rows if ascending
                        else:
                            data = data.tail(limit_value)  # Keep last N rows if descending
                    
                    # Create line chart
                    line = ax.plot(data['DATE'].values, data[data_column].values, marker='o', color='#6EC1A7', linewidth=2)
                    ax.set_ylabel(f'{data_column.replace("_", " ").title()}')
                    ax.set_title(f'{data_column.replace("_", " ").title()} Trends Over Time')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                    
                    # Add values on data points if requested
                    if show_values:
                        for i, value in enumerate(data[data_column].values):
                            ax.annotate(f'{value:,.0f}', 
                                      (data['DATE'].values[i], value),
                                      textcoords="offset points", 
                                      xytext=(0,10), 
                                      ha='center',
                                      color='white',
                                      fontweight='bold')
            
            # Adjust layout
            self.chart_figure.tight_layout()
            
            # Refresh the canvas
            self.chart_canvas.draw()
            
            if self.debug:
                print(f"Chart updated: {chart_type}")
                
        except Exception as e:
            if self.debug:
                print(f"Error updating chart: {str(e)}")
                traceback.print_exc()
            self.statusBar().showMessage(f"Error updating chart: {str(e)}")
    
    def save_chart(self):
        """Save the current chart to a file."""
        if not hasattr(self, 'chart_figure'):
            self.statusBar().showMessage("No chart to save")
            return
            
        try:
            # Get file name from dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Chart", 
                str(self.export_dir / "chart.png"),
                "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf);;SVG Image (*.svg)"
            )
            
            if not file_path:
                return  # User canceled
                
            # Save the figure
            self.chart_figure.savefig(
                file_path,
                dpi=300,
                bbox_inches='tight',
                facecolor=self.chart_figure.get_facecolor()
            )
            
            self.statusBar().showMessage(f"Chart saved to {file_path}")
            
        except Exception as e:
            self.statusBar().showMessage(f"Error saving chart: {str(e)}")
            if self.debug:
                print(f"Error saving chart: {str(e)}")
                traceback.print_exc()

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
        """Refresh the raw data table with the current processed data."""
        if self.processed_data is not None:
            # Check if we need to create a model
            self._create_raw_data_model()
            
            if self.debug:
                print(f"Updated raw data table with {len(self.processed_data)} rows")

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

    def toggle_value_selection(self):
        """
        Toggle the visibility of the value selection panel in the Raw Data tab.
        When checked, shows the panel and populates it with values.
        When unchecked, keeps the panel visible but clears it to maintain layout.
        """
        is_checked = self.show_value_selection.isChecked()
        
        if self.debug:
            print(f"Toggle value selection: state={is_checked}, is_visible={self.value_list_widget.isVisible()}")
        
        # Always keep the widget visible to maintain layout, but manage content
        self.value_list_widget.setVisible(True)
        
        # Clear the list if checkbox is unchecked
        if not is_checked:
            self.value_list.clear()
            # Disable the list and buttons when unchecked
            self.value_list.setEnabled(False)
            self.select_all_button.setEnabled(False)
            self.deselect_all_button.setEnabled(False)
        else:
            # Enable the list and buttons when checked
            self.value_list.setEnabled(True)
            self.select_all_button.setEnabled(True)
            self.deselect_all_button.setEnabled(True)
            # Update the options if we have data
            if self.raw_data is not None:
                self.update_filter_options()
        
        if self.debug:
            print(f"After toggle({is_checked}): widget is visible={self.value_list_widget.isVisible()}, list is enabled={self.value_list.isEnabled()}")

    def update_filter_options(self):
        """
        Update the filter options based on the selected column in the Raw Data tab.
        Populates the value list with unique values from the selected column.
        """
        if self.debug:
            print(f"update_filter_options called: value_list exists={hasattr(self, 'value_list')}, raw_data exists={self.raw_data is not None}")
        
        # Block signals during update to prevent recursive calls
        self.value_list.blockSignals(True)
        
        # Clear the list
        self.value_list.clear()
        
        try:
            column = self.column_selector.currentText()
            if not column or self.raw_data is None:
                if self.debug:
                    print(f"No column selected or no raw data available")
                return
            
            # Get unique values for the selected column
            unique_values = self.raw_data[column].unique()
            
            if self.debug:
                print(f"Updating filter options for column: {column}")
                print(f"Found {len(unique_values)} unique values for column {column}")
                print(f"First few values: {unique_values[:5].tolist() if len(unique_values) > 0 else []}")
            
            # Add unique values to the list
            for value in sorted(unique_values, key=str):
                self.value_list.addItem(str(value))
            
            # Select all values by default
            self.select_all_values()
            
            if self.debug:
                print(f"Added {len(unique_values)} unique values to value_list for column {column}")
                print(f"value_list now has {self.value_list.count()} items")
        except Exception as e:
            if self.debug:
                print(f"Error updating filter options: {str(e)}")
        finally:
            # Always unblock signals
            self.value_list.blockSignals(False)
            
            # Debug output about column selector state
            if self.debug:
                print(f"column_selector current text: {self.column_selector.currentText()}")
                print(f"column_selector current index: {self.column_selector.currentIndex()}")
                print(f"column_selector item count: {self.column_selector.count()}")

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
        if self.debug:
            print("\n--- UPDATE ANALYSIS VIEW ---")
        
        if not hasattr(self, 'processed_data') or self.processed_data is None:
            if self.debug:
                print("No processed data available, showing empty message")
            # Create an empty DataFrame with a message
            result = pd.DataFrame({"Message": ["No data loaded. Please import a CSV file."]})
            model = CustomTableModel(result)
            self.analysis_view.setModel(model)
            self.statusBar().showMessage("No data loaded for analysis")
            return
            
        analysis_type = self.analysis_selector.currentText()
        if self.debug:
            print(f"Selected analysis type: {analysis_type}")
        
        df = self.analysis_data.copy() if hasattr(self, 'analysis_data') and self.analysis_data is not None else self.processed_data.copy()
        
        if self.debug:
            print(f"Using data source: {'analysis_data' if hasattr(self, 'analysis_data') and self.analysis_data is not None else 'processed_data'}")
            print(f"Data shape: {df.shape}")
        
        try:
            # Check for required columns
            required_columns = {'PLAYER', 'SCORE', 'CHEST', 'SOURCE'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                # Create a message about missing columns
                missing_cols_str = ", ".join(missing_columns)
                if self.debug:
                    print(f"Missing required columns: {missing_cols_str}")
                self.statusBar().showMessage(f"Missing required columns: {missing_cols_str}")
                
                # Create a simple DataFrame with a message
                result = pd.DataFrame({
                    "Message": [f"Missing required columns: {missing_cols_str}"]
                })
                
                # Set the model with the error message
                model = CustomTableModel(result)
                self.analysis_view.setModel(model)
                return
            
            # Use the DataProcessor to analyze the data
            if self.debug:
                print("Calling DataProcessor.analyze_data...")
            from modules.dataprocessor import DataProcessor
            analysis_results = DataProcessor.analyze_data(df)
            
            if self.debug:
                print("Analysis complete, available result types:")
                for key in analysis_results.keys():
                    print(f"  - {key}: {analysis_results[key].shape if isinstance(analysis_results[key], pd.DataFrame) else 'not a DataFrame'}")
            
            # Display different results based on selected analysis type
            if analysis_type == "Player Overview":
                result = analysis_results['player_overview']
                if self.debug:
                    print(f"Selected 'player_overview' with shape {result.shape}")
                    print(f"Columns: {result.columns.tolist()}")
                    if not result.empty:
                        print(f"First row: {result.iloc[0].to_dict()}")
            elif analysis_type == "Player Totals":
                result = analysis_results['player_totals']
                if self.debug:
                    print(f"Selected 'player_totals' with shape {result.shape}")
            elif analysis_type == "Chest Totals":
                result = analysis_results['chest_totals']
                if self.debug:
                    print(f"Selected 'chest_totals' with shape {result.shape}")
            elif analysis_type == "Source Totals":
                result = analysis_results['source_totals']
                if self.debug:
                    print(f"Selected 'source_totals' with shape {result.shape}")
            elif analysis_type == "Date Totals":
                result = analysis_results['date_totals']
                if self.debug:
                    print(f"Selected 'date_totals' with shape {result.shape}")
            else:
                # Default to player overview
                result = analysis_results['player_overview']
                if self.debug:
                    print(f"No match for '{analysis_type}', defaulting to 'player_overview'")
            
            # Update the analysis table
            if self.debug:
                print(f"Creating table model with {len(result)} rows and {len(result.columns)} columns")
            model = CustomTableModel(result)
            self.analysis_view.setModel(model)
            self.analysis_view.resizeColumnsToContents()
            
            # Store the analysis results for chart generation
            self.analysis_results = analysis_results
            
            # Update status
            status_msg = f"Analysis updated: {analysis_type}"
            if self.debug:
                print(status_msg)
            self.statusBar().showMessage(status_msg)
            
        except Exception as e:
            error_msg = f"Error in analysis: {str(e)}"
            if self.debug:
                print(error_msg)
                traceback.print_exc()
            self.statusBar().showMessage(error_msg)
            log_error("Error in analysis", e, show_traceback=True)
        
        if self.debug:
            print("--- UPDATE ANALYSIS VIEW COMPLETE ---\n")

    def filter_analysis_data(self):
        """Apply filters to the analysis data."""
        # Similar to filter_raw_data, but for the analysis table
        # Implementation would go here
        pass

    def toggle_analysis_value_selection(self):
        """
        Toggle the visibility of the value selection panel in the Analysis tab.
        When checked, shows the panel and populates it with values.
        When unchecked, keeps the panel visible but clears it to maintain layout.
        """
        is_checked = self.analysis_show_value_selection.isChecked()
        
        if self.debug:
            print(f"Toggle analysis value selection: state={is_checked}, is_visible={self.analysis_value_panel.isVisible()}")
        
        # Always keep the panel visible to maintain layout, but manage content
        self.analysis_value_panel.setVisible(True)
        
        # Clear the list if checkbox is unchecked
        if not is_checked:
            self.analysis_value_list.clear()
            # Disable the list and buttons when unchecked
            self.analysis_value_list.setEnabled(False)
            self.select_all_analysis_button.setEnabled(False)
            self.deselect_all_analysis_button.setEnabled(False)
        else:
            # Enable the list and buttons when checked
            self.analysis_value_list.setEnabled(True)
            self.select_all_analysis_button.setEnabled(True)
            self.deselect_all_analysis_button.setEnabled(True)
            # Update the options if we have data
            if self.raw_data is not None:
                self.update_analysis_filter_options()
        
        if self.debug:
            print(f"After toggle({is_checked}): panel is visible={self.analysis_value_panel.isVisible()}, list is enabled={self.analysis_value_list.isEnabled()}")

    def select_all_analysis_values(self):
        """Select all values in the analysis value list."""
        if hasattr(self, 'analysis_value_list'):
            self.analysis_value_list.blockSignals(True)
            for i in range(self.analysis_value_list.count()):
                self.analysis_value_list.item(i).setSelected(True)
            self.analysis_value_list.blockSignals(False)
            if self.debug:
                print(f"Selected all {self.analysis_value_list.count()} values in analysis_value_list")

    def deselect_all_analysis_values(self):
        """Deselect all values in the analysis value list."""
        if hasattr(self, 'analysis_value_list'):
            self.analysis_value_list.blockSignals(True)
            for i in range(self.analysis_value_list.count()):
                self.analysis_value_list.item(i).setSelected(False)
            self.analysis_value_list.blockSignals(False)
            if self.debug:
                print(f"Deselected all {self.analysis_value_list.count()} values in analysis_value_list")

    def select_all_values(self):
        """Select all values in the value list."""
        if hasattr(self, 'value_list'):
            self.value_list.blockSignals(True)
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(True)
            self.value_list.blockSignals(False)
            if self.debug:
                print(f"Selected all {self.value_list.count()} values in value_list")
        
    def deselect_all_values(self):
        """Deselect all values in the value list."""
        if hasattr(self, 'value_list'):
            self.value_list.blockSignals(True)
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(False)
            self.value_list.blockSignals(False)
            if self.debug:
                print(f"Deselected all {self.value_list.count()} values in value_list")

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
            print(f"update_analysis_filter_options called: analysis_value_list exists={hasattr(self, 'analysis_value_list')}, raw_data exists={self.raw_data is not None}")
        
        # Get the selected column
        column = self.analysis_column_selector.currentText()
        if not column or self.raw_data is None:
            if self.debug:
                print("Exiting update_analysis_filter_options: no column selected or no data available")
            return
        
        if self.debug:
            print(f"Updating analysis filter options for column: {column}")
            
        # Block signals during update
        self.analysis_value_list.blockSignals(True)
        
        try:
            # Clear the analysis value list
            self.analysis_value_list.clear()
            if self.debug:
                print(f"Cleared analysis_value_list")
            
            # Get unique values from the selected column
            unique_values = self.raw_data[column].astype(str).unique().tolist()
            unique_values.sort()
            
            if self.debug:
                print(f"Found {len(unique_values)} unique values for column {column}")
                if len(unique_values) > 0:
                    print(f"First few values: {unique_values[:min(5, len(unique_values))]}")
            
            # Add the unique values to the analysis value list
            for value in unique_values:
                self.analysis_value_list.addItem(value)
            
            # Select all values by default
            self.select_all_analysis_values()
            
            if self.debug:
                print(f"Added {len(unique_values)} unique values to analysis_value_list")
                print(f"analysis_value_list now has {self.analysis_value_list.count()} items")
        except Exception as e:
            if self.debug:
                print(f"Error updating analysis filter options: {str(e)}")
                traceback.print_exc()
        finally:
            # Unblock signals
            self.analysis_value_list.blockSignals(False)

    def _create_raw_data_model(self):
        """Create and set the model for the raw data table."""
        from modules.customtablemodel import CustomTableModel
        
        # Create a model for the raw data table
        model = CustomTableModel(self.processed_data)
        
        # Set the model for the table
        if hasattr(self, 'raw_data_table'):
            self.raw_data_table.setModel(model)
            
            # Resize columns to content
            self.raw_data_table.resizeColumnsToContents()
            
            if self.debug:
                print(f"Created raw data model with {len(self.processed_data)} rows and {len(self.processed_data.columns)} columns")

    def setup_ui_components(self):
        """Set up the UI components."""
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        
        # Create tabs
        self.import_tab = QWidget()
        self.raw_data_tab = QWidget()
        self.analysis_tab = QWidget()
        self.charts_tab = QWidget()
        
        # Setup tabs
        self.setup_import_tab()
        self.setup_raw_data_tab()
        self.setup_analysis_tab()
        self.setup_charts_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.import_tab, "Import")
        self.tab_widget.addTab(self.raw_data_tab, "Raw Data")
        self.tab_widget.addTab(self.analysis_tab, "Analysis")
        self.tab_widget.addTab(self.charts_tab, "Charts")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        if self.debug:
            print("UI components initialized")

    def setup_import_tab(self):
        """Set up the Import tab."""
        # Set up layout
        layout = QVBoxLayout(self.import_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Add file label
        self.file_label = QLabel("No file loaded")
        self.file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_label)
        
        # Create import area
        self.import_area = ImportArea(self.import_tab, self.import_dir)
        
        # Add to import layout
        layout.addWidget(self.import_area)
        layout.addStretch()
        
        if self.debug:
            print("Import tab setup complete")

    def setup_raw_data_tab(self):
        """Set up the Raw Data tab."""
        # Set up layout
        layout = QVBoxLayout(self.raw_data_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create horizontal splitter for filter area and table
        raw_data_splitter = QSplitter(Qt.Horizontal)
        
        # Create left panel for filter controls
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
        column_layout.addWidget(self.column_selector)
        filter_layout.addLayout(column_layout)
        
        # Value selection toggle
        self.show_value_selection = QCheckBox("Select specific values")
        self.show_value_selection.setChecked(True)
        filter_layout.addWidget(self.show_value_selection)
        
        # Value selection area - Make it use all available vertical space
        self.value_list_widget = QWidget()
        value_list_layout = QVBoxLayout(self.value_list_widget)
        value_list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Value list with multiple selection - Set to expand vertically
        self.value_list = QListWidget()
        self.value_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.value_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        value_list_layout.addWidget(self.value_list, 1)  # Set stretch factor to 1 to use all available space
        
        # Value selection buttons
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)
        value_list_layout.addLayout(button_layout)
        
        # Add value selection to filter layout
        filter_layout.addWidget(self.value_list_widget, 1)  # Set stretch factor to 1 to use all available space
        
        # Make sure the widget is visible initially if checkbox is checked
        if self.debug:
            print(f"Raw data tab setup - setting initial visibility: {self.show_value_selection.isChecked()}")
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.apply_filter_button = QPushButton("Apply Filter")
        self.reset_filter_button = QPushButton("Clear Filter")
        action_layout.addWidget(self.apply_filter_button)
        action_layout.addWidget(self.reset_filter_button)
        filter_layout.addLayout(action_layout)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group, 1)  # Set stretch factor to 1 to use all available space
        left_layout.addStretch(0)  # Reduce the stretch factor to 0
        
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
        layout.addWidget(raw_data_splitter)
        
        if self.debug:
            print("Raw Data tab setup complete")

    def setup_analysis_tab(self):
        """Set up the Analysis tab."""
        # Set up layout
        layout = QVBoxLayout(self.analysis_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create horizontal splitter for analysis controls and table
        analysis_splitter = QSplitter(Qt.Horizontal)
        
        # Create left panel for analysis controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
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
        view_layout.addWidget(self.analysis_selector)
        filter_layout.addLayout(view_layout)
        
        # Column selector
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("Filter Column:"))
        self.analysis_column_selector = QComboBox()
        column_layout.addWidget(self.analysis_column_selector)
        filter_layout.addLayout(column_layout)
        
        # Value selection
        self.analysis_show_value_selection = QCheckBox("Select specific values")
        self.analysis_show_value_selection.setChecked(True)
        filter_layout.addWidget(self.analysis_show_value_selection)
        
        # Create value list widget - Make it use all available vertical space
        self.analysis_value_panel = QWidget()
        value_panel_layout = QVBoxLayout(self.analysis_value_panel)
        value_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Value list - Set to expand vertically
        self.analysis_value_list = QListWidget()
        self.analysis_value_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.analysis_value_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        value_panel_layout.addWidget(self.analysis_value_list, 1)  # Set stretch factor to 1 to use all available space
        
        # Select/Deselect buttons
        button_layout = QHBoxLayout()
        self.select_all_analysis_button = QPushButton("Select All")
        self.deselect_all_analysis_button = QPushButton("Deselect All")
        button_layout.addWidget(self.select_all_analysis_button)
        button_layout.addWidget(self.deselect_all_analysis_button)
        value_panel_layout.addLayout(button_layout)
        
        # Add value panel to filter layout
        filter_layout.addWidget(self.analysis_value_panel, 1)  # Set stretch factor to 1 to use all available space
        
        # Make sure the panel is visible initially if checkbox is checked
        if self.debug:
            print(f"Analysis tab setup - setting initial visibility: {self.analysis_show_value_selection.isChecked()}")
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.apply_analysis_filter_button = QPushButton("Apply Filter")
        self.reset_analysis_filter_button = QPushButton("Clear Filter")
        action_layout.addWidget(self.apply_analysis_filter_button)
        action_layout.addWidget(self.reset_analysis_filter_button)
        filter_layout.addLayout(action_layout)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group, 1)  # Set stretch factor to 1 to use all available space
        left_layout.addStretch(0)  # Reduce the stretch factor to 0
        
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
        layout.addWidget(analysis_splitter)
        
        if self.debug:
            print("Analysis tab setup complete")

    def setup_charts_tab(self):
        """Set up the Charts tab."""
        # Set up layout
        layout = QVBoxLayout(self.charts_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create chart controls panel
        chart_controls_group = QGroupBox("Chart Customization")
        chart_controls_layout = QGridLayout()
        
        # Chart type selection
        chart_controls_layout.addWidget(QLabel("Chart Type:"), 0, 0)
        self.analysis_chart_selector = QComboBox()
        self.analysis_chart_selector.addItems([
            "Player Totals",
            "Chest Totals",
            "Source Totals",
            "Date Totals"
        ])
        chart_controls_layout.addWidget(self.analysis_chart_selector, 0, 1)
        
        # Data column selection
        chart_controls_layout.addWidget(QLabel("Data Column:"), 0, 2)
        self.chart_data_column = QComboBox()
        self.chart_data_column.addItems(["SCORE", "CHEST_COUNT", "TOTAL_SCORE"])
        chart_controls_layout.addWidget(self.chart_data_column, 0, 3)
        
        # Sort options
        chart_controls_layout.addWidget(QLabel("Sort By:"), 1, 0)
        self.chart_sort_column = QComboBox()
        self.chart_sort_column.addItems(["SCORE", "CHEST_COUNT", "TOTAL_SCORE", "PLAYER", "DATE", "SOURCE", "CHEST"])
        chart_controls_layout.addWidget(self.chart_sort_column, 1, 1)
        
        chart_controls_layout.addWidget(QLabel("Sort Order:"), 1, 2)
        self.chart_sort_order = QComboBox()
        self.chart_sort_order.addItems(["Descending", "Ascending"])
        chart_controls_layout.addWidget(self.chart_sort_order, 1, 3)
        
        # Limit results
        chart_controls_layout.addWidget(QLabel("Limit Results:"), 2, 0)
        self.chart_limit_checkbox = QCheckBox("Show only top")
        chart_controls_layout.addWidget(self.chart_limit_checkbox, 2, 1)
        
        self.chart_limit_value = QSpinBox()
        self.chart_limit_value.setRange(1, 50)
        self.chart_limit_value.setValue(10)
        self.chart_limit_value.setSuffix(" items")
        chart_controls_layout.addWidget(self.chart_limit_value, 2, 2)
        
        # Display options
        chart_controls_layout.addWidget(QLabel("Display Options:"), 3, 0)
        self.chart_show_values = QCheckBox("Show values")
        self.chart_show_values.setChecked(True)
        chart_controls_layout.addWidget(self.chart_show_values, 3, 1)
        
        self.chart_show_grid = QCheckBox("Show grid")
        self.chart_show_grid.setChecked(True)
        chart_controls_layout.addWidget(self.chart_show_grid, 3, 2)
        
        # Action buttons
        self.apply_chart_options = QPushButton("Apply Options")
        chart_controls_layout.addWidget(self.apply_chart_options, 4, 0, 1, 2)
        
        self.save_chart_button = QPushButton("Save Chart")
        chart_controls_layout.addWidget(self.save_chart_button, 4, 2, 1, 2)
        
        # Set the layout for chart controls group
        chart_controls_group.setLayout(chart_controls_layout)
        layout.addWidget(chart_controls_group)
        
        # Create a matplotlib figure
        self.chart_figure = Figure(figsize=(10, 6), dpi=100)
        self.chart_canvas = FigureCanvas(self.chart_figure)
        
        # Set up the canvas to use most of the space
        self.chart_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chart_canvas, 1)  # Add with stretch factor 1 to use available space
        
        # Connect signals
        self.analysis_chart_selector.currentIndexChanged.connect(self.update_chart)
        self.apply_chart_options.clicked.connect(self.update_chart)
        self.save_chart_button.clicked.connect(self.save_chart)
        
        if self.debug:
            print("Charts tab setup complete")

    def apply_theme(self):
        """Apply the dark theme to the application."""
        # Get theme from configuration
        theme = self.config_manager.get_theme()
        
        # Apply the theme using StyleManager
        from modules.stylemanager import StyleManager
        StyleManager.apply_dark_theme(QApplication.instance())
        
        if self.debug:
            print("Applied dark theme to application")

    def on_tab_changed(self, index):
        """
        Handle tab widget changing to a different tab.
        
        Args:
            index (int): The index of the newly selected tab
        """
        if self.debug:
            print(f"Tab changed to index {index}")
        
        # Update UI based on the selected tab
        if index == 0:  # Import tab
            pass
        elif index == 1:  # Raw Data tab
            # Refresh raw data table
            self.update_raw_data_table()
        elif index == 2:  # Analysis tab
            # Refresh analysis view
            self.update_analysis_view()
        elif index == 3:  # Charts tab
            # Update chart
            self.update_chart()

    def connect_signals(self):
        """Connect signals to slots."""
        # File menu actions
        if hasattr(self, 'action_open_csv'):
            self.action_open_csv.triggered.connect(self.open_csv_file)
        if hasattr(self, 'action_quit'):
            self.action_quit.triggered.connect(self.close)
        
        # Help menu actions
        if hasattr(self, 'action_about'):
            self.action_about.triggered.connect(self.show_about_dialog)
        
        # Tab widget
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Import tab
        if hasattr(self, 'import_area'):
            self.import_area.fileSelected.connect(self.load_csv_file)
        
        # Raw Data tab
        if hasattr(self, 'column_selector'):
            self.column_selector.currentIndexChanged.connect(self.update_filter_options)
        if hasattr(self, 'show_value_selection'):
            self.show_value_selection.stateChanged.connect(self.toggle_value_selection)
        if hasattr(self, 'select_all_button'):
            self.select_all_button.clicked.connect(self.select_all_values)
        if hasattr(self, 'deselect_all_button'):
            self.deselect_all_button.clicked.connect(self.deselect_all_values)
        if hasattr(self, 'apply_filter_button'):
            self.apply_filter_button.clicked.connect(self.apply_filter)
        if hasattr(self, 'reset_filter_button'):
            self.reset_filter_button.clicked.connect(self.reset_filter)
        
        # Analysis tab
        if hasattr(self, 'analysis_column_selector'):
            self.analysis_column_selector.currentIndexChanged.connect(self.update_analysis_filter_options)
        if hasattr(self, 'analysis_show_value_selection'):
            self.analysis_show_value_selection.stateChanged.connect(self.toggle_analysis_value_selection)
        if hasattr(self, 'select_all_analysis_button'):
            self.select_all_analysis_button.clicked.connect(self.select_all_analysis_values)
        if hasattr(self, 'deselect_all_analysis_button'):
            self.deselect_all_analysis_button.clicked.connect(self.deselect_all_analysis_values)
        if hasattr(self, 'apply_analysis_filter_button'):
            self.apply_analysis_filter_button.clicked.connect(self.apply_analysis_filter)
        if hasattr(self, 'reset_analysis_filter_button'):
            self.reset_analysis_filter_button.clicked.connect(self.reset_analysis_filter)
        if hasattr(self, 'analysis_selector'):
            self.analysis_selector.currentIndexChanged.connect(self.update_analysis_view)
        if hasattr(self, 'analysis_chart_selector'):
            self.analysis_chart_selector.currentIndexChanged.connect(self.update_chart)
        
        if self.debug:
            print("Signals connected")

    def open_csv_file(self):
        """Open a CSV file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            str(self.import_dir),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.load_csv_file(file_path)

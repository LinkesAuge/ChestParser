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
    QListWidgetItem, QStatusBar, QGridLayout, QSizePolicy, QSpinBox, QDialog,
    QDialogButtonBox, QRadioButton
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
    
    def __init__(self, title="Total Battle Analyzer", debug=False):
        """
        Initialize the main window.
        
        Args:
            title (str, optional): Window title. Defaults to "Total Battle Analyzer".
            debug (bool, optional): Enable debug output. Defaults to False.
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
        
        if self.debug:
            print(f"Import directory: {self.import_dir}")
            print(f"Export directory: {self.export_dir}")
        
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
            # Use our enhanced DataProcessor for robust encoding detection and umlaut handling
            if self.debug:
                print("Using enhanced DataProcessor.read_csv_with_encoding_fix for better umlaut handling")
                print(f"File path type: {type(file_path)}")
                print(f"File path: {file_path}")
                print(f"Exists: {os.path.exists(file_path)}")
            
            # Enable debugging in DataProcessor temporarily
            old_debug = DataProcessor.debug
            DataProcessor.debug = self.debug
            
            # Try to load the file with our enhanced function
            df, success, error_message = DataProcessor.read_csv_with_encoding_fix(file_path)
            
            # Restore debug flag
            DataProcessor.debug = old_debug
            
            if not success:
                print(f"CSV loading error: {error_message}")
                self.show_error_dialog("Error Loading File", f"Failed to load CSV file: {error_message}")
                return False
                
            # Store the data
            self.raw_data = df.copy()
            
            if self.debug:
                print(f"Successfully loaded CSV file with enhanced umlaut handling")
                if 'PLAYER' in self.raw_data.columns:
                    print(f"Sample players: {self.raw_data['PLAYER'].head().tolist()}")
            
            # Apply additional text fixing to ensure all columns are properly processed
            try:
                text_columns = self.raw_data.select_dtypes(include=['object']).columns
                if self.debug:
                    print(f"Applying fix_dataframe_text to text columns: {text_columns.tolist()}")
                self.raw_data = DataProcessor.fix_dataframe_text(self.raw_data, columns=text_columns)
            except Exception as e:
                print(f"Warning: Error in additional text fixing: {str(e)}")
                # Continue even if text fixing fails
                
            # Convert SCORE to numeric
            if 'SCORE' in self.raw_data.columns:
                try:
                    self.raw_data['SCORE'] = pd.to_numeric(self.raw_data['SCORE'], errors='coerce')
                except Exception as e:
                    print(f"Warning: Error converting SCORE to numeric: {str(e)}")
            
            # Convert DATE to datetime
            if 'DATE' in self.raw_data.columns:
                try:
                    self.raw_data['DATE'] = pd.to_datetime(self.raw_data['DATE'], errors='coerce')
                except Exception as e:
                    print(f"Warning: Error converting DATE to datetime: {str(e)}")
            
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
            
            # Enable all tabs now that a CSV file is loaded
            self.enable_all_tabs()
            
            # Update the status bar to indicate successful loading
            self.statusBar().showMessage(f"CSV file loaded: {Path(file_path).name}")
                
            return True
                
        except Exception as e:
            error_msg = f"Error loading CSV file: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.show_error_dialog("Error Loading File", error_msg)
            return False

    def apply_filter(self):
        """Apply the filter to the raw data."""
        if self.raw_data is None:
            return
        
        # Get selected column
        column = self.column_selector.currentText()
        if not column:
            return
        
        # Create a fresh model to avoid stacking filters
        self._create_raw_data_model()
        
        # Get selected values
        selected_values = []
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            if item.isSelected():
                selected_values.append(item.text())
        
        # Apply filter
        if selected_values and hasattr(self, 'raw_data_proxy_model'):
            if self.debug:
                print(f"Applying filter on {column} with {len(selected_values)} selected values")
            
            # Store the selected values for reference
            self.processed_data = self.raw_data[self.raw_data[column].astype(str).isin(selected_values)]
            
            # Update the status message
            self.statusBar().showMessage(f"Filtered by {column}: {len(selected_values)} values selected")
        else:
            # No values selected or no proxy model
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
        """Update the chart based on the selected group by dimension, measure, chart type, and options."""
        if self.debug:
            print(f"Update chart called")
        
        # Check if we have necessary UI components
        if not hasattr(self, 'chart_group_by') or not hasattr(self, 'chart_measure') or not hasattr(self, 'chart_canvas'):
            if self.debug:
                print("Chart UI components not found")
            return
            
        # Check if we have analysis results
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            if self.debug:
                print("No analysis results available for charting")
            return
        
        try:
            # Get the selected options
            group_by_dimension = self.chart_group_by.currentText()
            measure = self.chart_measure.currentText()
            chart_type = self.chart_type_selector.currentText()
            
            # Map the group by dimension to the right data category for getting the correct dataset
            data_category = ""
            category_column = ""
            
            if group_by_dimension == "PLAYER":
                data_category = "Player Totals"
                category_column = 'PLAYER'
            elif group_by_dimension == "CHEST":
                data_category = "Chest Totals"
                category_column = 'CHEST'
            elif group_by_dimension == "SOURCE":
                data_category = "Source Totals"
                category_column = 'SOURCE'
            elif group_by_dimension == "DATE":
                data_category = "Date Totals"
                category_column = 'DATE'
            
            # Get sort options
            sort_column = self.chart_sort_column.currentText()
            sort_ascending = self.chart_sort_order.currentText() == "Ascending"
            
            # Get limit options
            limit_results = self.chart_limit_checkbox.isChecked()
            limit_value = self.chart_limit_value.value()
            
            # Get display options
            show_values = self.chart_show_values.isChecked()
            show_grid = self.chart_show_grid.isChecked()
            
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
            
            # Get data based on group by dimension (via data category mapping)
            if data_category == "Player Totals":
                data = self.analysis_results['player_totals'].copy()
                if self.debug:
                    print(f"Player Totals columns: {data.columns.tolist()}")
            elif data_category == "Chest Totals":
                data = self.analysis_results['chest_totals'].copy()
                if self.debug:
                    print(f"Chest Totals columns: {data.columns.tolist()}")
            elif data_category == "Source Totals":
                data = self.analysis_results['source_totals'].copy()
                if self.debug:
                    print(f"Source Totals columns: {data.columns.tolist()}")
            elif data_category == "Date Totals":
                data = self.analysis_results['date_totals'].copy()
                if self.debug:
                    print(f"Date Totals columns: {data.columns.tolist()}")
            else:
                if self.debug:
                    print(f"Unknown data category: {data_category}")
                return
            
            # Check if we have data to display
            if len(data) == 0:
                if self.debug:
                    print(f"No data available for {data_category}")
                return
            
            # Make sure the measure column exists in the dataset
            if measure not in data.columns:
                # Some analyses might have different column names
                if measure == "TOTAL_SCORE" and "SCORE" in data.columns:
                    measure = "SCORE"
                    if self.debug:
                        print(f"Using SCORE instead of TOTAL_SCORE")
                elif measure == "CHEST_COUNT" and "COUNT" in data.columns:
                    # We should not reach this now as we're adding CHEST_COUNT to all datasets,
                    # but keep as fallback
                    measure = "COUNT" 
                    if self.debug:
                        print(f"Using COUNT instead of CHEST_COUNT")
                else:
                    measure = "SCORE"  # Default fallback
                    if self.debug:
                        print(f"Using default fallback measure: SCORE")
                
                if self.debug:
                    print(f"Column {measure} not found, falling back to {measure}")
            
            # Sort data
            sort_by = sort_column
            # If sort column doesn't exist in this dataset, use the measure column
            if sort_column not in data.columns:
                sort_by = measure
                if self.debug:
                    print(f"Sort column {sort_column} not found, using {measure} instead")
            
            data = data.sort_values(sort_by, ascending=sort_ascending)
            if self.debug:
                print(f"Sorted data by {sort_by} (ascending={sort_ascending})")
            
            # Now apply limit to the sorted data
            if limit_results and len(data) > limit_value:
                # For descending order, we want the HIGHEST values, which are at the BEGINNING of the sorted data
                # For ascending order, we want the LOWEST values, which are at the BEGINNING of the sorted data
                data = data.head(limit_value)
                if self.debug:
                    print(f"Limited to top {limit_value} items after sorting")
            
            # Adjust category order based on the chart type
            # For horizontal bar charts, reverse the order to display in proper vertical order
            if chart_type == "Horizontal Bar" and not sort_ascending:
                data = data.iloc[::-1].reset_index(drop=True)
            
            # Create chart based on selected chart type
            chart_title = f"{group_by_dimension} by {measure}"
            
            if self.debug:
                print(f"Creating chart with title: {chart_title}")
                print(f"Using measure column: {measure}")
                if measure in data.columns:
                    print(f"Measure column values (first 5): {data[measure].head().tolist()}")
                else:
                    print(f"WARNING: Measure column '{measure}' not found in data!")
                    print(f"Available columns: {data.columns.tolist()}")
            
            if chart_type == "Bar Chart":
                bars = ax.bar(data[category_column].values, data[measure].values, color='#5991C4')
                ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                ax.set_title(chart_title)
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
                # Add values on top of each bar if requested
                if show_values:
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                               
            elif chart_type == "Horizontal Bar":
                bars = ax.barh(data[category_column].values, data[measure].values, color='#D4AF37')
                ax.set_xlabel(f'{measure.replace("_", " ").title()}')
                ax.set_title(chart_title)
                
                # Add values at the end of each bar if requested
                if show_values:
                    for i, bar in enumerate(bars):
                        value = data[measure].values[i]
                        ax.text(value, bar.get_y() + bar.get_height()/2, f" {value:,.0f}", 
                               va='center', color='white', fontweight='bold')
                
            elif chart_type == "Pie Chart":
                pie_colors = ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F', '#9966CC', '#F0C75A', '#527A96']
                wedges, texts, autotexts = ax.pie(
                    data[measure].values, 
                    labels=data[category_column].values, 
                    autopct='%1.1f%%' if show_values else '',
                    colors=pie_colors[:len(data)],
                    startangle=90,
                    wedgeprops={'edgecolor': '#1A2742', 'linewidth': 1}
                )
                for text in texts + autotexts:
                    text.set_color('white')
                for autotext in autotexts:
                    autotext.set_fontweight('bold')
                ax.set_title(f'{chart_title} Distribution')
                
            elif chart_type == "Line Chart":
                line = ax.plot(data[category_column].values, data[measure].values, marker='o', color='#6EC1A7', linewidth=2)
                ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                ax.set_title(f'{chart_title} Trends')
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
                # Add values on data points if requested
                if show_values:
                    for i, value in enumerate(data[measure].values):
                        ax.annotate(f'{value:,.0f}', 
                                  (data[category_column].values[i], value),
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
                print(f"Chart updated: {chart_type} for {group_by_dimension} by {measure}")
                
        except Exception as e:
            if self.debug:
                print(f"Error updating chart: {str(e)}")
                traceback.print_exc()
            self.statusBar().showMessage(f"Error updating chart: {str(e)}")
    
    def save_chart(self):
        """Save the current chart to a file or export data for spreadsheet use."""
        if not hasattr(self, 'chart_figure'):
            self.statusBar().showMessage("No chart to save")
            return
            
        try:
            # Get export options
            export_options = QDialog(self)
            export_options.setWindowTitle("Export Options")
            export_options.setMinimumWidth(300)
            
            export_layout = QVBoxLayout(export_options)
            
            export_type_group = QGroupBox("Export Type")
            export_type_layout = QVBoxLayout()
            
            image_radio = QRadioButton("Export as Image")
            image_radio.setChecked(True)
            data_radio = QRadioButton("Export Data for Excel/Sheets")
            
            export_type_layout.addWidget(image_radio)
            export_type_layout.addWidget(data_radio)
            export_type_group.setLayout(export_type_layout)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(export_options.accept)
            buttons.rejected.connect(export_options.reject)
            
            export_layout.addWidget(export_type_group)
            export_layout.addWidget(buttons)
            
            # Show dialog and get result
            if export_options.exec() != QDialog.Accepted:
                return
            
            # Determine export type
            export_as_image = image_radio.isChecked()
            
            if export_as_image:
                # Export as image (PNG, JPG, PDF, SVG)
                file_path, selected_filter = QFileDialog.getSaveFileName(
                    self, 
                    "Save Chart as Image", 
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
            else:
                # Export data as CSV for Excel/Google Sheets
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Export Chart Data", 
                    str(self.export_dir / "chart_data.csv"),
                    "CSV File (*.csv);;Excel File (*.xlsx)"
                )
                
                if not file_path:
                    return  # User canceled
                
                # Get the current chart data
                try:
                    # Get data based on group by dimension
                    group_by_dimension = self.chart_group_by.currentText()
                    data_category = ""
                    
                    if group_by_dimension == "PLAYER":
                        data_category = "Player Totals"
                        data = self.analysis_results['player_totals'].copy()
                    elif group_by_dimension == "CHEST":
                        data_category = "Chest Totals"
                        data = self.analysis_results['chest_totals'].copy()
                    elif group_by_dimension == "SOURCE":
                        data_category = "Source Totals"
                        data = self.analysis_results['source_totals'].copy()
                    elif group_by_dimension == "DATE":
                        data_category = "Date Totals"
                        data = self.analysis_results['date_totals'].copy()
                    else:
                        self.statusBar().showMessage(f"Unknown group by dimension: {group_by_dimension}")
                        return
                    
                    # Check if we have data to export
                    if len(data) == 0:
                        self.statusBar().showMessage(f"No data available to export")
                        return
                    
                    # Get the selected measure
                    measure = self.chart_measure.currentText()
                    
                    # Make sure the measure column exists in the dataset
                    if measure not in data.columns:
                        if self.debug:
                            print(f"Measure column '{measure}' not found in data! Available columns: {data.columns.tolist()}")
                        
                        # Some analyses might have different column names
                        if measure == "TOTAL_SCORE" and "SCORE" in data.columns:
                            measure = "SCORE"
                            if self.debug:
                                print(f"Using SCORE instead of TOTAL_SCORE for export")
                        else:
                            measure = "SCORE"  # Default fallback
                            if self.debug:
                                print(f"Using default fallback measure: SCORE for export")
                    
                    # Get the sorting options
                    sort_column = self.chart_sort_column.currentText()
                    sort_ascending = self.chart_sort_order.currentText() == "Ascending"
                    limit_results = self.chart_limit_checkbox.isChecked()
                    limit_value = self.chart_limit_value.value()
                    
                    # Apply sorting and limiting to match what's shown in the chart
                    sort_by = sort_column
                    if sort_column not in data.columns:
                        sort_by = measure
                        if self.debug:
                            print(f"Sort column {sort_column} not found, using {measure} instead")
                    
                    data = data.sort_values(sort_by, ascending=sort_ascending)
                    
                    if limit_results and len(data) > limit_value:
                        data = data.head(limit_value)
                    
                    # Export to file
                    if file_path.lower().endswith('.csv'):
                        # Use our new write_csv_with_umlauts function for proper umlaut handling
                        if not DataProcessor.write_csv_with_umlauts(data, file_path):
                            QMessageBox.warning(
                                self,
                                "CSV Export Error",
                                "Failed to export CSV file with proper encoding.",
                                QMessageBox.Ok
                            )
                            return
                    elif file_path.lower().endswith('.xlsx'):
                        try:
                            data.to_excel(file_path, index=False)
                        except ImportError:
                            # If openpyxl is not installed, show an error message
                            QMessageBox.warning(
                                self,
                                "Excel Export Error",
                                "Excel export requires the openpyxl package. Saving as CSV instead.",
                                QMessageBox.Ok
                            )
                            # Save as CSV instead with proper umlaut handling
                            file_path = file_path.replace('.xlsx', '.csv')
                            if not DataProcessor.write_csv_with_umlauts(data, file_path):
                                QMessageBox.warning(
                                    self,
                                    "CSV Export Error",
                                    "Failed to export CSV file with proper encoding.",
                                    QMessageBox.Ok
                                )
                                return
                    
                    self.statusBar().showMessage(f"Chart data exported to {file_path}")
                
                except Exception as e:
                    if self.debug:
                        print(f"Error exporting chart data: {str(e)}")
                        traceback.print_exc()
                    self.statusBar().showMessage(f"Error exporting chart data: {str(e)}")
        
        except Exception as e:
            if self.debug:
                print(f"Error saving chart: {str(e)}")
                traceback.print_exc()
            self.statusBar().showMessage(f"Error saving chart: {str(e)}")

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
        from PySide6.QtCore import QSortFilterProxyModel
        
        # Create a model for the raw data table
        source_model = CustomTableModel(self.processed_data)
        
        # Create a proxy model for sorting and filtering
        self.raw_data_proxy_model = QSortFilterProxyModel()
        self.raw_data_proxy_model.setSourceModel(source_model)
        
        # Set the proxy model for the table
        if hasattr(self, 'raw_data_table'):
            self.raw_data_table.setModel(self.raw_data_proxy_model)
            
            # Enable sorting
            self.raw_data_table.setSortingEnabled(True)
            
            # Resize columns to content
            self.raw_data_table.resizeColumnsToContents()
            
            if self.debug:
                print(f"Created raw data model with {len(self.processed_data)} rows and {len(self.processed_data.columns)} columns")
                print(f"Set up proxy model for raw data table for sorting and filtering")

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
        
        # Initially disable all tabs except Import (index 0)
        self.disable_tabs_except_import()
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        if self.debug:
            print("UI components initialized")
            
    def disable_tabs_except_import(self):
        """Disable all tabs except the Import tab (index 0)."""
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, False)
        
        # Apply greyed out styling to disabled tabs
        self.tab_widget.setStyleSheet("""
            QTabBar::tab:disabled {
                color: #666666;
                background-color: #1A2742;
            }
        """)
        
    def enable_all_tabs(self):
        """Enable all tabs."""
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)
            
        # Remove the disabled styling
        self.tab_widget.setStyleSheet("")
        
        # Apply the theme to ensure consistent styling
        self.apply_theme()

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
        
        # Add export button at the bottom
        export_layout = QHBoxLayout()
        self.export_raw_data_button = QPushButton("Export to CSV")
        export_layout.addWidget(self.export_raw_data_button)
        filter_layout.addLayout(export_layout)
        
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
        
        # Add export button at the bottom
        export_layout = QHBoxLayout()
        self.export_analysis_button = QPushButton("Export to CSV")
        export_layout.addWidget(self.export_analysis_button)
        filter_layout.addLayout(export_layout)
        
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
        layout.addWidget(analysis_splitter, 1)
        
        if self.debug:
            print("Analysis tab setup complete")

    def setup_charts_tab(self):
        """Set up the Charts tab."""
        # Set up layout
        layout = QVBoxLayout(self.charts_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create horizontal splitter for controls and chart
        charts_splitter = QSplitter(Qt.Horizontal)
        
        # Create left panel for chart controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        # Create chart controls group
        chart_controls_group = QGroupBox("Chart Customization")
        chart_controls_layout = QVBoxLayout()
        chart_controls_layout.setSpacing(10)
        
        # Chart type selection
        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_selector = QComboBox()
        self.chart_type_selector.addItems([
            "Bar Chart",
            "Horizontal Bar",
            "Pie Chart",
            "Line Chart"
        ])
        chart_type_layout.addWidget(self.chart_type_selector)
        chart_controls_layout.addLayout(chart_type_layout)
        
        # NEW: Two-step data selection
        # 1. Group By (dimension)
        group_by_layout = QHBoxLayout()
        group_by_layout.addWidget(QLabel("Group By:"))
        self.chart_group_by = QComboBox()
        self.chart_group_by.addItems([
            "PLAYER",
            "CHEST",
            "SOURCE",
            "DATE"
        ])
        group_by_layout.addWidget(self.chart_group_by)
        chart_controls_layout.addLayout(group_by_layout)
        
        # 2. Measure (metric)
        measure_layout = QHBoxLayout()
        measure_layout.addWidget(QLabel("Measure:"))
        self.chart_measure = QComboBox()
        self.chart_measure.addItems([
            "SCORE",
            "CHEST_COUNT",
            "TOTAL_SCORE"
        ])
        measure_layout.addWidget(self.chart_measure)
        chart_controls_layout.addLayout(measure_layout)
        
        # For compatibility with existing code
        self.chart_data_category = QComboBox()
        self.chart_data_category.addItems([
            "Player Totals",
            "Chest Totals",
            "Source Totals",
            "Date Totals"
        ])
        self.chart_data_category.setVisible(False)  # Hide the old dropdown
        self.chart_data_column = QComboBox()
        self.chart_data_column.addItems(["SCORE", "CHEST_COUNT", "TOTAL_SCORE"])
        self.chart_data_column.setVisible(False)  # Hide the old dropdown
        
        # Sorting group
        sorting_group = QGroupBox("Sorting Options")
        sorting_layout = QVBoxLayout()
        
        # Sort column
        sort_column_layout = QHBoxLayout()
        sort_column_layout.addWidget(QLabel("Sort By:"))
        self.chart_sort_column = QComboBox()
        self.chart_sort_column.addItems(["SCORE", "CHEST_COUNT", "TOTAL_SCORE"])
        sort_column_layout.addWidget(self.chart_sort_column)
        sorting_layout.addLayout(sort_column_layout)
        
        # Sort order
        sort_order_layout = QHBoxLayout()
        sort_order_layout.addWidget(QLabel("Sort Order:"))
        self.chart_sort_order = QComboBox()
        self.chart_sort_order.addItems(["Descending", "Ascending"])
        sort_order_layout.addWidget(self.chart_sort_order)
        sorting_layout.addLayout(sort_order_layout)
        
        # Limit results
        limit_layout = QHBoxLayout()
        self.chart_limit_checkbox = QCheckBox("Show only top")
        limit_layout.addWidget(self.chart_limit_checkbox)
        
        self.chart_limit_value = QSpinBox()
        self.chart_limit_value.setRange(1, 50)
        self.chart_limit_value.setValue(10)
        self.chart_limit_value.setSuffix(" items")
        # The styling is now applied globally in StyleManager
        limit_layout.addWidget(self.chart_limit_value)
        limit_layout.addStretch()
        sorting_layout.addLayout(limit_layout)
        
        # Finalize sorting group
        sorting_group.setLayout(sorting_layout)
        chart_controls_layout.addWidget(sorting_group)
        
        # Display options group
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout()
        
        # Display checkboxes
        self.chart_show_values = QCheckBox("Show values")
        self.chart_show_values.setChecked(True)
        display_layout.addWidget(self.chart_show_values)
        
        self.chart_show_grid = QCheckBox("Show grid")
        self.chart_show_grid.setChecked(True)
        display_layout.addWidget(self.chart_show_grid)
        
        # Finalize display group
        display_group.setLayout(display_layout)
        chart_controls_layout.addWidget(display_group)
        
        # Action buttons
        action_layout = QVBoxLayout()
        
        # Remove the Apply Options button as we'll make all controls update immediately
        # self.apply_chart_options = QPushButton("Apply Options")
        # action_layout.addWidget(self.apply_chart_options)
        
        self.save_chart_button = QPushButton("Save Chart")
        action_layout.addWidget(self.save_chart_button)
        
        # Add button layout to main layout
        chart_controls_layout.addLayout(action_layout)
        
        # Add stretch to push controls to the top
        chart_controls_layout.addStretch(1)
        
        # Set the layout for chart controls group
        chart_controls_group.setLayout(chart_controls_layout)
        left_layout.addWidget(chart_controls_group, 1)
        
        # Add left panel to splitter
        charts_splitter.addWidget(left_panel)
        
        # Create right panel for chart
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create a matplotlib figure
        self.chart_figure = Figure(dpi=100)
        self.chart_canvas = FigureCanvas(self.chart_figure)
        
        # Set up the canvas to use all available space
        self.chart_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.chart_canvas, 1)
        
        # Add right panel to splitter
        charts_splitter.addWidget(right_panel)
        
        # Set splitter sizes (30% controls, 70% chart)
        charts_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        layout.addWidget(charts_splitter, 1)
        
        # Connect signals - make all controls update immediately
        self.chart_group_by.currentIndexChanged.connect(self.update_chart_data_category)
        self.chart_measure.currentIndexChanged.connect(self.update_chart_data_column)
        self.chart_group_by.currentIndexChanged.connect(self.update_chart)
        self.chart_measure.currentIndexChanged.connect(self.update_chart)
        self.chart_type_selector.currentIndexChanged.connect(self.update_chart)
        # Connect the remaining controls to update_chart for immediate updates
        self.chart_sort_column.currentIndexChanged.connect(self.update_chart)
        self.chart_sort_order.currentIndexChanged.connect(self.update_chart)
        self.chart_limit_checkbox.stateChanged.connect(self.update_chart)
        self.chart_limit_value.valueChanged.connect(self.update_chart)
        self.chart_show_values.stateChanged.connect(self.update_chart)
        self.chart_show_grid.stateChanged.connect(self.update_chart)
        # Connect the save button to the save_chart method
        self.save_chart_button.clicked.connect(self.save_chart)
        
        if self.debug:
            print("Charts tab setup complete")
            
    def update_chart_data_category(self):
        """Update the data category based on the selected Group By dimension.
        
        This updates the internal chart_data_category combobox which is still used
        by other functions for compatibility.
        """
        if not hasattr(self, 'chart_group_by'):
            return
            
        # Get the selected group by dimension
        group_by = self.chart_group_by.currentText()
        
        # Update the hidden data category combobox (for compatibility)
        if group_by == "PLAYER":
            self.chart_data_category.setCurrentText("Player Totals")
        elif group_by == "CHEST":
            self.chart_data_category.setCurrentText("Chest Totals")
        elif group_by == "SOURCE":
            self.chart_data_category.setCurrentText("Source Totals")
        elif group_by == "DATE":
            self.chart_data_category.setCurrentText("Date Totals")
            
        # Update the available measures based on the group by dimension
        self.update_available_measures()
            
        # Update the chart
        self.update_chart()
            
    def update_available_measures(self):
        """Update the available measures based on the selected Group By dimension."""
        if not hasattr(self, 'chart_group_by') or not hasattr(self, 'chart_measure'):
            return
            
        # Save current selection if possible
        current_measure = self.chart_measure.currentText() if self.chart_measure.count() > 0 else ""
            
        # Clear existing items
        self.chart_measure.clear()
        
        # Get the selected group by dimension
        group_by = self.chart_group_by.currentText()
        
        # Add appropriate measure options based on group by dimension
        if group_by == "PLAYER":
            self.chart_measure.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by == "CHEST":
            self.chart_measure.addItems(["SCORE", "CHEST_COUNT"])
        elif group_by == "SOURCE":
            self.chart_measure.addItems(["SCORE", "CHEST_COUNT"])
        elif group_by == "DATE":
            self.chart_measure.addItems(["SCORE", "CHEST_COUNT"])
        
        # Restore previous selection if it's still valid
        index = self.chart_measure.findText(current_measure)
        if index >= 0:
            self.chart_measure.setCurrentIndex(index)
        
        # Update the sort column options as well
        self.update_sort_options()
        
    def update_sort_options(self):
        """Update the available sort options based on the selected Group By dimension and Measure."""
        if not hasattr(self, 'chart_group_by') or not hasattr(self, 'chart_sort_column'):
            return
            
        # Save current selection if possible
        current_sort = self.chart_sort_column.currentText() if self.chart_sort_column.count() > 0 else ""
            
        # Clear existing items
        self.chart_sort_column.clear()
        
        # Get the selected group by dimension and measure
        group_by = self.chart_group_by.currentText()
        measure = self.chart_measure.currentText() if hasattr(self, 'chart_measure') else ""
        
        # Add appropriate sort options based on group by dimension
        if group_by == "PLAYER":
            self.chart_sort_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE", "PLAYER"])
        elif group_by == "CHEST":
            self.chart_sort_column.addItems(["SCORE", "CHEST_COUNT", "CHEST_TYPE"])
        elif group_by == "SOURCE":
            self.chart_sort_column.addItems(["SCORE", "CHEST_COUNT", "SOURCE"])
        elif group_by == "DATE":
            self.chart_sort_column.addItems(["SCORE", "CHEST_COUNT", "DATE"])
        
        # Restore previous selection if it's still valid, otherwise select the measure
        index = self.chart_sort_column.findText(current_sort)
        if index >= 0:
            self.chart_sort_column.setCurrentIndex(index)
        elif measure:
            index = self.chart_sort_column.findText(measure)
            if index >= 0:
                self.chart_sort_column.setCurrentIndex(index)
    
    def update_chart_data_column(self):
        """Update the data column based on the selected Measure.
        
        This updates the internal chart_data_column combobox which is still used
        by other functions for compatibility.
        """
        if not hasattr(self, 'chart_measure'):
            return
            
        # Get the selected measure
        measure = self.chart_measure.currentText()
        
        # Now we directly set the measure to the column name since they match
        # (CHEST_COUNT, SCORE, etc.) in all datasets
        self.chart_data_column.setCurrentText(measure)
                
        if self.debug:
            print(f"Update chart data column: Measure={measure}, Selected Column={self.chart_data_column.currentText()}")
            
        # Update the chart
        self.update_chart()

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
        if hasattr(self, 'export_raw_data_button'):
            self.export_raw_data_button.clicked.connect(self.export_raw_data)
        
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
        if hasattr(self, 'export_analysis_button'):
            self.export_analysis_button.clicked.connect(self.export_analysis_data)
        if hasattr(self, 'analysis_selector'):
            self.analysis_selector.currentIndexChanged.connect(self.update_analysis_view)

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

    def export_raw_data(self):
        """Export the currently displayed raw data to a CSV file."""
        if not hasattr(self, 'raw_data_table') or not hasattr(self, 'processed_data'):
            self.statusBar().showMessage("No data to export")
            return
            
        try:
            # Get the current filtered data from the proxy model
            if hasattr(self, 'raw_data_proxy_model'):
                model = self.raw_data_proxy_model
                
                # Get the number of rows and columns in the proxy model
                rows = model.rowCount()
                cols = model.columnCount()
                
                if rows == 0 or cols == 0:
                    self.statusBar().showMessage("No data to export after filtering")
                    return
                    
                # Get the source model (CustomTableModel)
                source_model = model.sourceModel()
                
                # Get the header names
                headers = [source_model.headerData(col, Qt.Horizontal) for col in range(cols)]
                
                # Create a new DataFrame to hold the filtered data
                filtered_data = pd.DataFrame(columns=headers)
                
                # Populate the DataFrame with filtered data
                for row in range(rows):
                    row_data = {}
                    for col in range(cols):
                        # Map the proxy model index to the source model index
                        source_index = model.mapToSource(model.index(row, col))
                        
                        # Get the data from the source model
                        value = source_model.data(source_index, Qt.DisplayRole)
                        
                        # Add to row data dictionary
                        row_data[headers[col]] = value
                    
                    # Add the row to the DataFrame
                    filtered_data.loc[row] = row_data
                
                # If we have no data after filtering, show a message
                if filtered_data.empty:
                    self.statusBar().showMessage("No data to export after filtering")
                    return
                    
                # Check export directory
                export_dir = self.config_manager.get_export_directory()
                
                # Create the export directory if it doesn't exist
                if not os.path.exists(export_dir):
                    Path(export_dir).mkdir(parents=True, exist_ok=True)
                
                # Default filename
                default_filename = str(Path(export_dir) / "raw_data_export.csv")
                
                # Show save dialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export Raw Data", default_filename, "CSV Files (*.csv)"
                )
                
                if not file_path:
                    return  # User canceled
                
                # Use DataProcessor to write CSV with proper umlaut handling
                if DataProcessor.write_csv_with_umlauts(filtered_data, file_path):
                    self.statusBar().showMessage(f"Raw data exported to {file_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Export Error",
                        "Failed to export data to CSV. See console for details.",
                        QMessageBox.Ok
                    )
            else:
                self.statusBar().showMessage("No filtered data available to export")
        except Exception as e:
            if self.debug:
                print(f"Error exporting raw data: {str(e)}")
                traceback.print_exc()
            self.statusBar().showMessage(f"Error exporting data: {str(e)}")
            QMessageBox.warning(
                self,
                "Export Error",
                f"An error occurred while exporting: {str(e)}",
                QMessageBox.Ok
            )
    
    def export_analysis_data(self):
        """Export the current analysis view to a CSV file."""
        if not hasattr(self, 'analysis_view') or not hasattr(self, 'analysis_results'):
            self.statusBar().showMessage("No analysis data to export")
            return
            
        try:
            # Get the current analysis view
            current_view = self.analysis_selector.currentText()
            
            # Get the appropriate DataFrame based on the selected view
            if current_view == "Player Totals":
                df = self.analysis_results['player_totals'].copy()
            elif current_view == "Chest Totals":
                df = self.analysis_results['chest_totals'].copy()
            elif current_view == "Source Totals":
                df = self.analysis_results['source_totals'].copy()
            elif current_view == "Date Totals":
                df = self.analysis_results['date_totals'].copy()
            elif current_view == "Player Overview":
                df = self.analysis_results['player_overview'].copy()
            else:
                self.statusBar().showMessage(f"Unknown analysis view: {current_view}")
                return
            
            # If we have a proxy model, get the filtered data
            if hasattr(self, 'analysis_proxy_model'):
                model = self.analysis_proxy_model
                source_model = model.sourceModel()
                
                # Get the column count and header names
                cols = source_model.columnCount()
                headers = [source_model.headerData(col, Qt.Horizontal) for col in range(cols)]
                
                # Get the row count from the filtered model
                rows = model.rowCount()
                
                if rows == 0:
                    self.statusBar().showMessage("No data to export after filtering")
                    return
                
                # Create a new DataFrame for filtered data
                filtered_data = pd.DataFrame(columns=headers)
                
                # Populate the DataFrame with filtered data
                for row in range(rows):
                    row_data = {}
                    for col in range(cols):
                        # Map the proxy model index to the source model index
                        source_index = model.mapToSource(model.index(row, col))
                        
                        # Get the data from the source model
                        value = source_model.data(source_index, Qt.DisplayRole)
                        
                        # Add to row data dictionary
                        row_data[headers[col]] = value
                    
                    # Add the row to the DataFrame
                    filtered_data.loc[row] = row_data
                
                # Use the filtered data for export
                df = filtered_data
            
            # Check if we have data to export
            if df is None or df.empty:
                self.statusBar().showMessage("No data available for export")
                return
            
            # Check export directory
            export_dir = self.config_manager.get_export_directory()
            
            # Create the export directory if it doesn't exist
            if not os.path.exists(export_dir):
                Path(export_dir).mkdir(parents=True, exist_ok=True)
            
            # Default filename
            default_filepath = str(Path(export_dir) / f"{current_view.lower().replace(' ', '_')}_export.csv")
            
            # Show save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Analysis", default_filepath, "CSV Files (*.csv)"
            )
            
            if not file_path:
                return  # User canceled
            
            # Use DataProcessor to write CSV with proper umlaut handling
            if DataProcessor.write_csv_with_umlauts(df, file_path):
                self.statusBar().showMessage(f"Analysis data exported to {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    "Failed to export data to CSV. See console for details.",
                    QMessageBox.Ok
                )
                
        except Exception as e:
            if self.debug:
                print(f"Error exporting analysis data: {str(e)}")
                traceback.print_exc()
            self.statusBar().showMessage(f"Error exporting data: {str(e)}")
            QMessageBox.warning(
                self,
                "Export Error",
                f"An error occurred while exporting: {str(e)}",
                QMessageBox.Ok
            )

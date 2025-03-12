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
import time

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
from PySide6.QtGui import QIcon, QColor, QAction
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
    
    def __init__(self, debug=False):
        """
        Initialize the main window.
        
        Args:
            debug (bool, optional): Enable debug output. Defaults to False.
        """
        super().__init__()
        
        # Debug mode flag
        self.debug = debug
        
        # Initialize data storage
        self.raw_data = None
        self.processed_data = None
        self.analysis_data = None
        self.analysis_results = None
        self.last_loaded_file = None
        
        # Add a timestamp for the last file load to prevent rapid successive loads
        self.last_file_load_time = 0
        
        # Flag to prevent multiple file dialogs
        self._file_dialog_active = False
        
        # Setup UI components
        self.setup_ui_components()
        
        # Connect signals
        self.connect_signals()
        
        # Set window properties
        self.setWindowTitle("Chest Parser")
        self.resize(1200, 800)
        
        # Initialize tabs as disabled until data is loaded
        self.disable_tabs_except_import()
        
        # Initialize the configuration manager
        self.config_manager = ConfigManager()
        
        # Initialize the import area with the config manager
        if hasattr(self, 'import_area'):
            self.import_area.set_config_manager(self.config_manager)
        
        # Initialize the export area with the config manager
        if hasattr(self, 'export_area'):
            self.export_area.set_config_manager(self.config_manager)
        
        # Initialize the analysis value selection panel visibility
        if hasattr(self, 'analysis_show_value_selection') and hasattr(self, 'analysis_value_panel'):
            if self.debug:
                print(f"Analysis tab - initializing with analysis_show_value_selection checked: {self.analysis_show_value_selection.isChecked()}")
            self.toggle_analysis_value_selection()
        
        # Set status message
        self.statusBar().showMessage("Ready")
    
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
        import traceback  # Import at the beginning of the method
        import time
        
        if self.debug:
            print(f"\n--- LOAD CSV FILE CALLED WITH: {file_path} ---\n")
            traceback.print_stack()  # Print stack trace to identify caller
        
        # Convert file_path to Path object for consistent handling
        file_path = Path(file_path)
        
        # Check if we're trying to load the same file again
        if self.last_loaded_file == str(file_path.absolute()):
            if self.debug:
                print(f"File already loaded, skipping reload: {file_path}")
            # File already processed, just ensure tabs are enabled and return success
            self.enable_all_tabs()
            self.statusBar().showMessage(f"File already loaded: {file_path.name}")
            return True
        
        # Debounce mechanism - prevent multiple calls in quick succession (within 1.5 seconds)
        current_time = time.time()
        if hasattr(self, 'last_file_load_time') and (current_time - self.last_file_load_time < 1.5):
            if self.debug:
                print(f"Ignoring rapid successive file load request: {file_path}")
                print(f"Time since last load: {current_time - self.last_file_load_time:.2f} seconds")
            return True
        
        # Update the last load time
        self.last_file_load_time = current_time
        
        if self.debug:
            print(f"\n--- PROCESSING NEW CSV FILE: {file_path} ---\n")
        
        try:
            # Use our enhanced DataProcessor for robust encoding detection and umlaut handling
            if self.debug:
                print("Using enhanced DataProcessor.read_csv_with_encoding_fix for better umlaut handling")
                print(f"File path type: {type(file_path)}")
                print(f"File path: {file_path}")
                print(f"Exists: {file_path.exists()}")
            
            # Enable debugging in DataProcessor temporarily if our debug is enabled
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
            
            # Store the file path so we don't reload the same file
            self.last_loaded_file = str(file_path.absolute())
            
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
            
            # Process data for analysis
            self.process_data()
            
            # Enable all tabs since we have data
            self.enable_all_tabs()
            
            # Update chart
            self.update_chart()
            
            # Update status message
            self.statusBar().showMessage(f"Loaded {len(self.raw_data)} rows from {file_path.name}")
            
            # Success
            if self.debug:
                print(f"Successfully loaded and processed {file_path.name}")
                
            return True
                
        except Exception as e:
            error_message = f"Error loading CSV file: {str(e)}"
            print(error_message)
            traceback.print_exc()
            self.show_error_dialog("Error Loading File", error_message)
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
        if not hasattr(self, 'chart_data_category') or not hasattr(self, 'chart_data_column') or not hasattr(self, 'chart_canvas'):
            if self.debug:
                print("Chart UI components not found")
            return
            
        # Check if we have analysis results
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            if self.debug:
                print("No analysis results available for charting")
            return
        
        try:
            # Clear the figure and axes to prevent overlapping charts
            self.chart_canvas.fig.clear()
            
            # Get the selected options
            group_by_dimension = self.chart_data_category.currentText()
            measure = self.chart_data_column.currentText()
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
            limit_results = self.chart_limit_enabled.isChecked()
            limit_value = self.chart_limit_value.value()
            
            # Get display options
            show_values = self.chart_show_values.isChecked()
            show_grid = self.chart_show_grid.isChecked()
            
            # Get chart colors
            TABLEAU_COLORS = self.chart_canvas.get_tableau_colors()
            
            # Set grid visibility according to user preference
            ax = self.chart_canvas.fig.add_subplot(111)
            self.chart_canvas.apply_style_to_axes(ax)
            ax.grid(show_grid, color=self.chart_canvas.style_presets['default']['grid_color'], 
                  linestyle='--', linewidth=0.5, alpha=0.7)
            
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
                # Create a list of colors for each bar (cycle through the palette)
                colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                
                # Create the bar chart with varied colors
                bars = ax.bar(data[category_column].values, data[measure].values, color=colors)
                
                ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                ax.set_title(chart_title)
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
                # Add values on top of each bar if requested
                if show_values:
                    # Clear any existing value texts first to prevent duplicates
                    for text in ax.texts:
                        text.remove()
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:,.0f}', ha='center', va='bottom', 
                               color=self.chart_canvas.style_presets['default']['text_color'], 
                               fontweight='bold')
                               
            elif chart_type == "Horizontal Bar":
                # Create a list of colors for each bar (cycle through the palette)
                colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                
                # Create the horizontal bar chart with varied colors
                bars = ax.barh(data[category_column].values, data[measure].values, color=colors)
                
                ax.set_xlabel(f'{measure.replace("_", " ").title()}')
                ax.set_title(chart_title)
                
                # Add values at the end of each bar if requested
                if show_values:
                    # Clear any existing value texts first to prevent duplicates
                    for text in ax.texts:
                        text.remove()
                    
                    # Clear any existing value texts first to prevent duplicates
                    for text in ax.texts:
                        text.remove()
                        
                    for i, bar in enumerate(bars):
                        value = data[measure].values[i]
                        ax.text(value, bar.get_y() + bar.get_height()/2, f" {value:,.0f}", 
                               va='center', 
                               color=self.chart_canvas.style_presets['default']['text_color'], 
                               fontweight='bold')
                
            elif chart_type == "Pie Chart":
                # Calculate smaller data sample if too many slices would make pie chart unreadable
                # Clear any existing texts to prevent duplicates
                for text in ax.texts:
                    text.remove()
                
                pie_data = data
                if len(data) > 10:
                    # Limit to top 9 + "Others"
                    top_items = data.iloc[:9].copy()
                    others_sum = data.iloc[9:][measure].sum()
                    others_row = pd.DataFrame({
                        category_column: ['Others'],
                        measure: [others_sum]
                    })
                    pie_data = pd.concat([top_items, others_row]).reset_index(drop=True)
                
                # Clear any existing texts to prevent duplicates
                for text in ax.texts:
                    text.remove()
                
                # Use multiple colors from TABLEAU_COLORS for pie slices (cycle if needed)
                colors_to_use = []
                for i in range(len(pie_data)):
                    colors_to_use.append(TABLEAU_COLORS[i % len(TABLEAU_COLORS)])
                    
                wedges, texts, autotexts = ax.pie(
                    pie_data[measure].values, 
                    labels=pie_data[category_column].values, 
                    autopct='%1.1f%%' if show_values else '',
                    colors=colors_to_use,
                    startangle=90,
                    wedgeprops={'edgecolor': self.chart_canvas.style_presets['default']['bg_color'], 'linewidth': 1}
                )
                # Style the pie chart text
                # For date data, a line chart makes sense as a single line
                if category_column == 'DATE':
                    # Sort data by date for line chart to ensure proper chronological order
                    data = data.sort_values(category_column)
                    
                    line = ax.plot(data[category_column].values, data[measure].values, 
                                  marker='o', color=TABLEAU_COLORS[2],  # Green
                                  linewidth=2, markersize=8)
                    
                    # Add values at each point if requested
                    if show_values:
                        # Clear any existing value texts first to prevent duplicates
                        for text in ax.texts:
                            text.remove()
                        
                        for i, (x, y) in enumerate(zip(data[category_column].values, data[measure].values)):
                            ax.text(x, y, f'{y:,.0f}', ha='center', va='bottom',
                                   color=self.chart_canvas.style_presets['default']['text_color'],
                                   fontweight='bold')
                    
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Trends')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                else:
                    # For non-date categories, create a line chart with points at regular intervals
                    x = np.arange(len(data))
                    line = ax.plot(x, data[measure].values, 
                                  marker='o', color=TABLEAU_COLORS[2],  # Green
                                  linewidth=2, markersize=8)
                    
                    # Add values at each point if requested
                    if show_values:
                        # Clear any existing value texts first to prevent duplicates
                        for text in ax.texts:
                            text.remove()
                        
                        for i, y in enumerate(data[measure].values):
                            ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom',
                                   color=self.chart_canvas.style_presets['default']['text_color'],
                                   fontweight='bold')
                    
                    # Set x-ticks to category names
                    ax.set_xticks(x)
                    ax.set_xticklabels(data[category_column].values)
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Trends')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                else:
                    # For non-date categories, create a line chart with points at regular intervals
                    x = np.arange(len(data))
                    line = ax.plot(x, data[measure].values, 
                                  marker='o', color=TABLEAU_COLORS[2],  # Green
                                  linewidth=2, markersize=8)
                    
                    # Add values at each point if requested
                    if show_values:
                        for i, y in enumerate(data[measure].values):
                            ax.text(i, y, f'{y:,.0f}', ha='center', va='bottom',
                                   color=self.chart_canvas.style_presets['default']['text_color'],
                                   fontweight='bold')
                    
                    # Set x-ticks to category names
                    ax.set_xticks(x)
                    ax.set_xticklabels(data[category_column].values)
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Trends')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            else:
                    # For non-date categories, use a scatter plot with different colors
                    for i, (category, value) in enumerate(zip(data[category_column].values, data[measure].values)):
                        color_index = i % len(TABLEAU_COLORS)
                        ax.scatter(i, value, 
                                color=TABLEAU_COLORS[color_index],
                                s=100, zorder=10)
                        
                        # Connect points with lines if there are more than one
                        if i > 0:
                            # Draw line between points
                            ax.plot([i-1, i], [data[measure].values[i-1], value], 
                                  color=TABLEAU_COLORS[color_index % len(TABLEAU_COLORS)],
                                  linewidth=1.5, alpha=0.7, zorder=5)
                    
                    # Set the x-tick positions and labels        
                    ax.set_xticks(range(len(data)))
                    ax.set_xticklabels(data[category_column].values)
                    ax.set_ylabel(f'{measure.replace("_", " ").title()}')
                    ax.set_title(f'{chart_title} Comparison')
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
                # Add values on data points if requested
            if show_values:
                    if category_column == 'DATE':
                        for i, value in enumerate(data[measure].values):
                            ax.annotate(f'{value:,.0f}', 
                                    (data[category_column].values[i], value),
                                    textcoords="offset points", 
                                    xytext=(0,10), 
                                    ha='center',
                                        color=self.chart_canvas.style_presets['default']['text_color'],
                                        fontweight='bold')
                    else:
                        for i, value in enumerate(data[measure].values):
                            ax.annotate(f'{value:,.0f}', 
                                      (i, value),
                                      textcoords="offset points", 
                                      xytext=(0,10), 
                                      ha='center',
                                      color=self.chart_canvas.style_presets['default']['text_color'],
                                  fontweight='bold')
            
            # Adjust layout
            self.chart_canvas.fig.tight_layout()
            
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
        """Save the current chart as an image file."""
        try:
            # Make sure we have a chart to save
            if not hasattr(self, 'chart_canvas') or self.chart_canvas is None:
                QMessageBox.warning(self, "Save Error", "No chart to save.")
            return
            
            # Get export directory from config
            export_dir = Path(self.config_manager.get_export_directory())
            if not export_dir.exists():
                export_dir.mkdir(parents=True, exist_ok=True)

            # Generate a default filename based on chart data
            if hasattr(self, 'chart_data_category') and hasattr(self, 'chart_data_column'):
                category = self.chart_data_category.currentText()
                column = self.chart_data_column.currentText()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                default_filename = f"Chart_{category}_{column}_{timestamp}"
            else:
                default_filename = f"Chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Show file dialog
            file_formats = "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf);;SVG Image (*.svg)"
            filepath, selected_filter = QFileDialog.getSaveFileName(
                self, "Save Chart", str(export_dir / default_filename), file_formats
            )
            
            if not filepath:
                return
                
            # Save the directory for next time
            self.config_manager.set_export_directory(str(Path(filepath).parent))
            
            # Get file extension from selected filter
            if selected_filter == "PNG Image (*.png)":
                if not filepath.lower().endswith('.png'):
                    filepath += '.png'
                self.chart_canvas.figure.savefig(filepath, format='png', dpi=300, bbox_inches='tight', 
                                              facecolor='#1A2742', edgecolor='none')
            elif selected_filter == "JPEG Image (*.jpg)":
                if not filepath.lower().endswith('.jpg'):
                    filepath += '.jpg'
                self.chart_canvas.figure.savefig(filepath, format='jpg', dpi=300, bbox_inches='tight',
                                              facecolor='#1A2742', edgecolor='none')
            elif selected_filter == "PDF Document (*.pdf)":
                if not filepath.lower().endswith('.pdf'):
                    filepath += '.pdf'
                self.chart_canvas.figure.savefig(filepath, format='pdf', bbox_inches='tight',
                                             facecolor='#1A2742', edgecolor='none')
            elif selected_filter == "SVG Image (*.svg)":
                if not filepath.lower().endswith('.svg'):
                    filepath += '.svg'
                self.chart_canvas.figure.savefig(filepath, format='svg', bbox_inches='tight',
                                             facecolor='#1A2742', edgecolor='none')
                
            # Show success message
            QMessageBox.information(self, "Save Successful", f"Chart saved to:\n{filepath}")
            
        except Exception as e:
            log_error("Error saving chart", e)
            QMessageBox.warning(self, "Save Error", f"An error occurred while saving the chart: {str(e)}")
            
    def export_chart_data(self):
        """Export the current chart data to a CSV or Excel file."""
        try:
            # Make sure we have data to export
            if self.analysis_results is None or not self.analysis_results:
                QMessageBox.warning(self, "Export Error", "No data to export.")
                return
            
            # Get export directory from config
            export_dir = Path(self.config_manager.get_export_directory())
            if not export_dir.exists():
                export_dir.mkdir(parents=True, exist_ok=True)
                
            # Get the current data category and column
            if not hasattr(self, 'chart_data_category') or not hasattr(self, 'chart_data_column'):
                QMessageBox.warning(self, "Export Error", "No chart data configuration available.")
                return
                
            category = self.chart_data_category.currentText()
            
            # Determine which dataset to use
            if category == "PLAYER":
                dataset_key = 'player_totals'
            elif category == "CHEST":
                dataset_key = 'chest_totals'
            elif category == "SOURCE":
                dataset_key = 'source_totals'
            elif category == "DATE":
                dataset_key = 'date_totals'
            else:
                QMessageBox.warning(self, "Export Error", f"Unknown data category: {category}")
                return
                
            # Get the data from analysis results
            if dataset_key in self.analysis_results and not self.analysis_results[dataset_key].empty:
                df = self.analysis_results[dataset_key].copy()
            else:
                QMessageBox.warning(self, "Export Error", f"No data available for {dataset_key}.")
                return
                    
            # Generate a default filename based on chart data
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"ChartData_{category}_{timestamp}"

            # Show file dialog
            file_formats = "CSV Files (*.csv);;Excel Files (*.xlsx)"
            filepath, selected_filter = QFileDialog.getSaveFileName(
                self, "Export Chart Data", str(export_dir / default_filename), file_formats
            )
            
            if not filepath:
                return
                
            # Save the directory for next time
            self.config_manager.set_export_directory(str(Path(filepath).parent))
            
            # Apply current sorting
            sort_column = self.chart_sort_column.currentText()
            ascending = self.chart_sort_order.currentText() == "Ascending"
            
            if sort_column in df.columns:
                df = df.sort_values(by=sort_column, ascending=ascending)
                
            # Apply current limit if enabled
            if self.chart_limit_enabled.isChecked():
                limit = self.chart_limit_value.value()
                df = df.head(limit)
            
            # Export the data
            if selected_filter == "CSV Files (*.csv)":
                if not filepath.lower().endswith('.csv'):
                    filepath += '.csv'
                    
                # Use the improved CSV writing function from DataProcessor
                DataProcessor.write_csv_with_umlauts(df, filepath)
                    
            elif selected_filter == "Excel Files (*.xlsx)":
                if not filepath.lower().endswith('.xlsx'):
                    filepath += '.xlsx'
                df.to_excel(filepath, index=False)
                
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Chart data exported to:\n{filepath}")
        
        except Exception as e:
            log_error("Error exporting chart data", e)
            traceback.print_exc()
            QMessageBox.warning(self, "Export Error", f"An error occurred while exporting the chart data: {str(e)}")

    def process_data(self):
        """Process the loaded data to prepare it for analysis and visualization."""
        if not hasattr(self, 'raw_data') or self.raw_data is None:
            if self.debug:
                print("No data to process")
            return
        
        try:
            if self.debug:
                print("Starting data processing...")
            # Make a copy of the data
            df = self.raw_data.copy()
            
            # Check for required columns
            required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
            
            if self.debug:
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
        self.report_tab = QWidget()
        
        # Setup tabs
        self.setup_import_tab()
        self.setup_raw_data_tab()
        self.setup_analysis_tab()
        self.setup_charts_tab()
        self.setup_report_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.import_tab, "Import")
        self.tab_widget.addTab(self.raw_data_tab, "Raw Data")
        self.tab_widget.addTab(self.analysis_tab, "Analysis")
        self.tab_widget.addTab(self.charts_tab, "Charts")
        self.tab_widget.addTab(self.report_tab, "Report")
        
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
        
    def apply_theme(self):
        """Apply the dark theme to specific UI components that need custom styling."""
        # Set stylesheet for QTabBar
        self.tab_widget.setStyleSheet(f"""
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
                font-weight: bold;
                color: {DARK_THEME['accent']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {DARK_THEME['accent_hover']};
            }}
        """)
        
        # Refresh the UI to apply changes
        self.update()

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
        self.import_area = ImportArea(self.import_tab, debug=self.debug)
        
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
        # Create chart tab layout
        main_layout = QVBoxLayout(self.charts_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create horizontal splitter for control panel and chart
        chart_splitter = QSplitter(Qt.Horizontal)
        
        # Left control panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(5)
        
        # Group data selection controls
        data_group = QGroupBox("Data Selection")
        data_layout = QVBoxLayout()
        
        # Two-step data selection process
        # Step 1: Group By dimension selector
        group_by_layout = QHBoxLayout()
        group_by_layout.addWidget(QLabel("Group By:"))
        self.chart_data_category = QComboBox()
        self.chart_data_category.addItems(["PLAYER", "CHEST", "SOURCE", "DATE"])
        group_by_layout.addWidget(self.chart_data_category)
        data_layout.addLayout(group_by_layout)
        
        # Step 2: Measure value selector
        measure_layout = QHBoxLayout()
        measure_layout.addWidget(QLabel("Measure:"))
        self.chart_data_column = QComboBox()
        # Will be populated based on Group By selection
        measure_layout.addWidget(self.chart_data_column)
        data_layout.addLayout(measure_layout)
        
        # Chart type selector
        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_selector = QComboBox()
        self.chart_type_selector.addItems(["Bar Chart", "Horizontal Bar", "Pie Chart", "Line Chart"])
        chart_type_layout.addWidget(self.chart_type_selector)
        data_layout.addLayout(chart_type_layout)
        
        # Sorting options
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Sort By:"))
        self.chart_sort_column = QComboBox()
        # Will be populated based on Group By selection
        sort_layout.addWidget(self.chart_sort_column)
        data_layout.addLayout(sort_layout)
        
        sort_order_layout = QHBoxLayout()
        self.chart_sort_order = QComboBox()
        self.chart_sort_order.addItems(["Descending", "Ascending"])
        sort_order_layout.addWidget(self.chart_sort_order)
        data_layout.addLayout(sort_order_layout)
        
        # Limit options
        limit_layout = QHBoxLayout()
        self.chart_limit_enabled = QCheckBox("Show only top")
        self.chart_limit_enabled.setChecked(True)
        limit_layout.addWidget(self.chart_limit_enabled)
        
        self.chart_limit_value = QSpinBox()
        self.chart_limit_value.setMinimum(1)
        self.chart_limit_value.setMaximum(100)
        self.chart_limit_value.setValue(10)
        limit_layout.addWidget(self.chart_limit_value)
        
        data_layout.addLayout(limit_layout)
        
        data_group.setLayout(data_layout)
        control_layout.addWidget(data_group)
        
        # Display options group
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout()
        
        # Value labels
        self.chart_show_values = QCheckBox("Show values on chart")
        self.chart_show_values.setChecked(True)
        display_layout.addWidget(self.chart_show_values)
        
        # Grid lines
        self.chart_show_grid = QCheckBox("Show grid lines")
        self.chart_show_grid.setChecked(True)
        display_layout.addWidget(self.chart_show_grid)
        
        display_group.setLayout(display_layout)
        control_layout.addWidget(display_group)
        
        # Export options group
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout()
        
        # Save chart as image
        self.save_chart_button = QPushButton("Save Chart as Image")
        export_layout.addWidget(self.save_chart_button)
        
        # Export chart data
        self.export_chart_data_button = QPushButton("Export Chart Data")
        export_layout.addWidget(self.export_chart_data_button)
        
        export_group.setLayout(export_layout)
        control_layout.addWidget(export_group)
        
        # Add spacer at bottom to push controls to top
        control_layout.addStretch()
        
        # Add control panel to splitter
        chart_splitter.addWidget(control_panel)
        
        # Create matplotlib canvas for the chart
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_canvas = MplCanvas(width=8, height=6, dpi=100)
        chart_layout.addWidget(self.chart_canvas)
        
        # Add chart to splitter
        chart_splitter.addWidget(chart_container)
        
        # Set initial splitter sizes (30% controls, 70% chart)
        chart_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        main_layout.addWidget(chart_splitter)
        
        # Connect signals for chart controls
        self.chart_data_category.currentIndexChanged.connect(self.update_available_measures)
        self.chart_data_category.currentIndexChanged.connect(self.update_sort_options)
        self.chart_data_category.currentIndexChanged.connect(self.update_chart)
        
        self.chart_data_column.currentIndexChanged.connect(self.update_chart)
        self.chart_type_selector.currentIndexChanged.connect(self.update_chart)
        self.chart_sort_column.currentIndexChanged.connect(self.update_chart)
        self.chart_sort_order.currentIndexChanged.connect(self.update_chart)
        self.chart_limit_enabled.stateChanged.connect(self.update_chart)
        self.chart_limit_value.valueChanged.connect(self.update_chart)
        self.chart_show_values.stateChanged.connect(self.update_chart)
        self.chart_show_grid.stateChanged.connect(self.update_chart)
        
        # Connect save/export buttons
        self.save_chart_button.clicked.connect(self.save_chart)
        self.export_chart_data_button.clicked.connect(self.export_chart_data)
        
        # Update measures based on initial Group By selection
        self.update_available_measures()
        self.update_sort_options()
        
        # Update chart with initial selection
        self.update_chart()
        
        if self.debug:
            print("Charts tab setup complete")
            
    def setup_report_tab(self):
        """
        Set up the Report tab UI with comprehensive reporting capabilities.
        
        Creates a tab with controls for generating different types of reports,
        options to include various report elements, and a text browser for
        displaying the generated report. Also includes buttons for generating
        and exporting reports.
        """
        # Create report tab widget if it doesn't exist
        self.report_tab = QWidget()
        main_layout = QVBoxLayout(self.report_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create report controls in a group
        controls_group = QGroupBox("Report Controls")
        controls_layout = QGridLayout()

        # Row 1: Report type selector
        controls_layout.addWidget(QLabel("Report Type:"), 0, 0)
        self.report_type_selector = QComboBox()
        self.report_type_selector.addItems([
            "Full Report",
            "Player Performance",
            "Chest Type Analysis",
            "Source Analysis"
        ])
        controls_layout.addWidget(self.report_type_selector, 0, 1)

        # Row 2: Include options
        controls_layout.addWidget(QLabel("Include:"), 1, 0)

        include_layout = QHBoxLayout()

        self.include_charts_checkbox = QCheckBox("Charts")
        self.include_charts_checkbox.setChecked(True)
        include_layout.addWidget(self.include_charts_checkbox)

        self.include_tables_checkbox = QCheckBox("Tables")
        self.include_tables_checkbox.setChecked(True)
        include_layout.addWidget(self.include_tables_checkbox)

        self.include_stats_checkbox = QCheckBox("Statistics")
        self.include_stats_checkbox.setChecked(True)
        include_layout.addWidget(self.include_stats_checkbox)

        include_layout.addStretch()
        controls_layout.addLayout(include_layout, 1, 1)

        # Action buttons row
        button_layout = QHBoxLayout()

        # Generate report button
        self.generate_report_button = QPushButton("Generate Report")
        button_layout.addWidget(self.generate_report_button)

        # Export report button
        self.export_report_button = QPushButton("Export Report")
        button_layout.addWidget(self.export_report_button)

        # Add button layout to controls
        controls_layout.addLayout(button_layout, 2, 0, 1, 2)
        
        # Set the layout for the controls group
        controls_group.setLayout(controls_layout)
        
        # Add the controls group to the main layout
        main_layout.addWidget(controls_group)
        
        # Create a text browser for displaying the report
        self.report_view = QTextBrowser()
        self.report_view.setOpenExternalLinks(True)
        self.report_view.setMinimumHeight(400)  # Set a minimum height for better visibility
        
        # Add a welcome message
        welcome_html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
                h1, h2 { color: #2c3e50; }
                .container { text-align: center; margin-top: 50px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Total Battle Analyzer - Report Generator</h1>
                <h2>Select report options and click "Generate Report" to create a report</h2>
                <p>You can include charts, tables, and statistics in your report.</p>
                <p>Once generated, you can export the report as HTML or PDF.</p>
            </div>
        </body>
        </html>
        """
        self.report_view.setHtml(welcome_html)
        
        # Add the report view to the main layout
        main_layout.addWidget(self.report_view)
        
        # Add the report tab to the main tab widget
        self.tab_widget.addTab(self.report_tab, "Report")

    def generate_chart_for_report(self, chart_type, category_field, title):
        """
        Generate a chart image for the report.
        
        This helper method creates a chart image file that can be included in HTML reports.
        Uses multiple colors for different chart elements to ensure consistency with the
        main application's chart styling.
        
        Args:
            chart_type (str): The type of chart to generate (e.g., 'Bar Chart', 'Pie Chart')
            category_field (str): The field to use for categorization (e.g., 'PLAYER', 'CHEST')
            title (str): The title of the chart
            
        Returns:
            str: The path to the generated chart image file, or None on failure
        """
        try:
            # Create a temporary file for the chart
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_file.close()
            
            # Determine which dataset to use based on category_field
            if category_field == 'PLAYER':
                if 'player_totals' not in self.analysis_results or self.analysis_results['player_totals'].empty:
                    return None
                df = self.analysis_results['player_totals']
            elif category_field == 'CHEST':
                if 'chest_totals' not in self.analysis_results or self.analysis_results['chest_totals'].empty:
                    return None
                df = self.analysis_results['chest_totals']
            elif category_field == 'SOURCE':
                if 'source_totals' not in self.analysis_results or self.analysis_results['source_totals'].empty:
                    return None
                df = self.analysis_results['source_totals']
            elif category_field == 'DATE':
                if 'date_totals' not in self.analysis_results or self.analysis_results['date_totals'].empty:
                    return None
                df = self.analysis_results['date_totals']
            else:
                return None
            
            # Create a temporary MplCanvas to get consistent styling and colors
            temp_canvas = MplCanvas(width=10, height=6)
            
            # Create the figure for the chart using MplCanvas style
            plt.figure(figsize=(10, 6), facecolor=temp_canvas.style_presets['default']['bg_color'])
            
            # Set the style for the chart - dark background with white text
            plt.style.use('dark_background')
            
            # Get current axis
            ax = plt.gca()
            
            # Set axis colors using MplCanvas styling
            ax.set_facecolor(temp_canvas.style_presets['default']['bg_color'])
            ax.xaxis.label.set_color(temp_canvas.style_presets['default']['text_color'])
            ax.yaxis.label.set_color(temp_canvas.style_presets['default']['text_color'])
            ax.title.set_color(temp_canvas.style_presets['default']['title_color'])
            ax.tick_params(colors=temp_canvas.style_presets['default']['text_color'])
            
            # Get consistent colors from MplCanvas
            TABLEAU_COLORS = temp_canvas.get_tableau_colors()
            
            # Generate the appropriate type of chart
            if chart_type == 'Bar Chart':
                if category_field == 'PLAYER':
                    # Use TOTAL_SCORE for players if available
                    score_col = 'TOTAL_SCORE' if 'TOTAL_SCORE' in df.columns else 'SCORE'
                    data = df.sort_values(score_col, ascending=False).head(15)  # Limit to top 15 for readability
                    
                    # Create a list of colors for each bar (cycle through the palette)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                    
                    bars = plt.bar(data['PLAYER'], data[score_col], color=colors)
                    plt.xticks(rotation=45, ha='right', color=temp_canvas.style_presets['default']['text_color'])
                    plt.ylabel('Score', color=temp_canvas.style_presets['default']['text_color'])
                    plt.title('Player Total Scores', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Add values on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                              f'{height:,.0f}', ha='center', va='bottom', 
                              color=temp_canvas.style_presets['default']['text_color'], 
                              fontweight='bold')
                    
                elif category_field == 'CHEST':
                    data = df.sort_values('SCORE', ascending=False)
                    
                    # Create a list of colors for each bar (cycle through the palette)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                    
                    bars = plt.bar(data['CHEST'], data['SCORE'], color=colors)
                    plt.xticks(rotation=45, ha='right', color=temp_canvas.style_presets['default']['text_color'])
                    plt.ylabel('Score', color=temp_canvas.style_presets['default']['text_color'])
                    plt.title('Scores by Chest Type', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Add values on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                              f'{height:,.0f}', ha='center', va='bottom', 
                              color=temp_canvas.style_presets['default']['text_color'], 
                              fontweight='bold')
                    
                elif category_field == 'SOURCE':
                    data = df.sort_values('SCORE', ascending=False)
                    
                    # Create a list of colors for each bar (cycle through the palette)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                    
                    bars = plt.bar(data['SOURCE'], data['SCORE'], color=colors)
                    plt.xticks(rotation=45, ha='right', color=temp_canvas.style_presets['default']['text_color'])
                    plt.ylabel('Score', color=temp_canvas.style_presets['default']['text_color'])
                    plt.title('Scores by Source', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Add values on top of bars
                    for bar in bars:
                        height = bar.get_height()
                        plt.text(bar.get_x() + bar.get_width()/2., height,
                              f'{height:,.0f}', ha='center', va='bottom', 
                              color=temp_canvas.style_presets['default']['text_color'], 
                              fontweight='bold')
                    
                elif category_field == 'DATE':
                    # For dates, sort chronologically
                    data = df.sort_values('DATE')
                    
                    # Create a list of colors for each bar (cycle through the palette)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                    
                    # Use line chart for date data
                    plt.plot(data['DATE'], data['SCORE'], marker='o', 
                           color=TABLEAU_COLORS[0],  # Gold from TABLEAU_COLORS
                           linewidth=2, markersize=8)
                    plt.xticks(rotation=45, ha='right', color=temp_canvas.style_presets['default']['text_color'])
                    plt.ylabel('Score', color=temp_canvas.style_presets['default']['text_color'])
                    plt.title('Scores by Date', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    plt.grid(True, alpha=0.3, color=temp_canvas.style_presets['default']['grid_color'])
                    
                    # Add values on data points
                    for i, value in enumerate(data['SCORE']):
                        plt.annotate(f'{value:,.0f}', 
                                  (data['DATE'].iloc[i], value),
                                  textcoords="offset points", 
                                  xytext=(0,10), 
                                  ha='center',
                                  color=temp_canvas.style_presets['default']['text_color'],
                                  fontweight='bold')
                
            elif chart_type == 'Pie Chart':
                if category_field == 'CHEST':
                    data = df.sort_values('SCORE', ascending=False)
                    
                    # If we have too many slices, limit to top 9 + "Others"
                    if len(data) > 10:
                        top_items = data.iloc[:9].copy()
                        others_sum = data.iloc[9:]['SCORE'].sum()
                        others_row = pd.DataFrame({
                            'CHEST': ['Others'],
                            'SCORE': [others_sum]
                        })
                        data = pd.concat([top_items, others_row]).reset_index(drop=True)
                    
                    # Create color list for pie slices (one color per slice)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                        
                    wedges, texts, autotexts = plt.pie(
                        data['SCORE'], 
                        labels=data['CHEST'], 
                        autopct='%1.1f%%', 
                        startangle=90, 
                        colors=colors,
                        wedgeprops={'edgecolor': temp_canvas.style_presets['default']['bg_color'], 'linewidth': 1}
                    )
                    plt.axis('equal')
                    plt.title('Chest Type Distribution by Score', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Make text visible on dark background
                    for text in texts:
                        text.set_color(temp_canvas.style_presets['default']['text_color'])
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        
                elif category_field == 'SOURCE':
                    data = df.sort_values('SCORE', ascending=False)
                    
                    # If we have too many slices, limit to top 9 + "Others"
                    if len(data) > 10:
                        top_items = data.iloc[:9].copy()
                        others_sum = data.iloc[9:]['SCORE'].sum()
                        others_row = pd.DataFrame({
                            'SOURCE': ['Others'],
                            'SCORE': [others_sum]
                        })
                        data = pd.concat([top_items, others_row]).reset_index(drop=True)
                    
                    # Create color list for pie slices (one color per slice)
                    colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                        
                    wedges, texts, autotexts = plt.pie(
                        data['SCORE'], 
                        labels=data['SOURCE'], 
                        autopct='%1.1f%%', 
                        startangle=90, 
                        colors=colors,
                        wedgeprops={'edgecolor': temp_canvas.style_presets['default']['bg_color'], 'linewidth': 1}
                    )
                    plt.axis('equal')
                    plt.title('Source Distribution by Score', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Make text visible on dark background
                    for text in texts:
                        text.set_color(temp_canvas.style_presets['default']['text_color'])
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                
            elif chart_type == 'Stacked Bar Chart' and category_field == 'PLAYER':
                # Get the player and source columns
                player_col = 'PLAYER'
                
                # Get columns that represent sources (but not the special columns)
                data_cols = [col for col in df.columns if col not in 
                            ['PLAYER', 'TOTAL_SCORE', 'CHEST_COUNT', 'AVG_SCORE']]
                
                if data_cols:
                    # Sort by total score
                    if 'TOTAL_SCORE' in df.columns:
                        data = df.sort_values('TOTAL_SCORE', ascending=False).head(10)  # Limit to top 10
                    else:
                        data = df.head(10)  # Just use first 10 rows if no TOTAL_SCORE
                    
                    # Create the stacked bar chart with consistent colors
                    bottom = np.zeros(len(data))
                    for i, col in enumerate(data_cols):
                        if col in data.columns:
                            values = data[col].fillna(0).values
                            plt.bar(data[player_col], values, bottom=bottom, 
                                   label=col, color=TABLEAU_COLORS[i % len(TABLEAU_COLORS)])
                            bottom += values
                    
                    plt.xticks(rotation=45, ha='right', color=temp_canvas.style_presets['default']['text_color'])
                    plt.ylabel('Score', color=temp_canvas.style_presets['default']['text_color'])
                    plt.title('Player Scores by Source', color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
                    
                    # Customize legend
                    legend = plt.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left')
                    legend.get_title().set_color(temp_canvas.style_presets['default']['text_color'])
                    for text in legend.get_texts():
                        text.set_color(temp_canvas.style_presets['default']['text_color'])
                    
                    plt.tight_layout()
            
            elif chart_type == 'Bubble Chart' and category_field == 'PLAYER':
                # Check if we have the necessary columns
                if 'TOTAL_SCORE' in df.columns and 'CHEST_COUNT' in df.columns:
                    # Filter out any rows with zeroes to avoid divide by zero
                    data = df[(df['TOTAL_SCORE'] > 0) & (df['CHEST_COUNT'] > 0)]
                    
                    if not data.empty:
                        # Calculate efficiency for sizing the bubbles
                        efficiency = data['TOTAL_SCORE'] / data['CHEST_COUNT']
                        
                        # Calculate sizes proportional to efficiency
                        max_size = 1000
                        min_size = 100
                        if efficiency.max() > efficiency.min():
                            size_scale = ((efficiency - efficiency.min()) / 
                                         (efficiency.max() - efficiency.min())) * (max_size - min_size) + min_size
                        else:
                            size_scale = np.ones(len(efficiency)) * max_size
                        
                        # Create the bubble chart with colors from TABLEAU_COLORS
                        colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                        scatter = plt.scatter(data['CHEST_COUNT'], data['TOTAL_SCORE'], 
                                            s=size_scale, alpha=0.7, 
                                            c=colors)
                        
                        # Add player labels
                        for i, player in enumerate(data['PLAYER']):
                            plt.annotate(player, 
                                        (data['CHEST_COUNT'].iloc[i], data['TOTAL_SCORE'].iloc[i]),
                                        xytext=(5, 5), textcoords='offset points',
                                        color=temp_canvas.style_presets['default']['text_color'], 
                                        fontweight='bold')
                        
                        plt.xlabel('Chest Count', color=temp_canvas.style_presets['default']['text_color'])
                        plt.ylabel('Total Score', color=temp_canvas.style_presets['default']['text_color'])
                        plt.title('Player Efficiency (Score vs Chest Count)', 
                                color=temp_canvas.style_presets['default']['title_color'], fontsize=14)
            
            # Set spine colors to match theme
            for spine in ax.spines.values():
                spine.set_color(temp_canvas.style_presets['default']['grid_color'])
            
            # Setup grid
            ax.grid(True, color=temp_canvas.style_presets['default']['grid_color'], linestyle='--', alpha=0.3)
            
            # Adjust layout and save with transparent background
            plt.tight_layout()
            plt.savefig(temp_file.name, format='png', dpi=150, bbox_inches='tight', 
                      facecolor=temp_canvas.style_presets['default']['bg_color'], 
                      edgecolor='none')
            plt.close()
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error generating chart for report: {e}")
            traceback.print_exc()
            return None

    def update_available_measures(self):
        """
        Update the available measures in the chart_data_column combobox based on the selected Group By dimension.
        This ensures that only relevant measures are displayed for each data category.
        """
        if not hasattr(self, 'chart_data_category') or not hasattr(self, 'chart_data_column'):
            if hasattr(self, 'debug') and self.debug:
                print("Chart UI components not found in update_available_measures")
            return
            
        group_by_dimension = self.chart_data_category.currentText()
        
        # Block signals to prevent triggering updates while updating the combobox
        self.chart_data_column.blockSignals(True)
            
        # Clear existing items
        self.chart_data_column.clear()

        # Populate measures based on the selected dimension
        if group_by_dimension == "PLAYER":
            self.chart_data_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "CHEST":
            self.chart_data_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "SOURCE":
            self.chart_data_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "DATE":
            self.chart_data_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_VALUE"])
        
        # Unblock signals
        self.chart_data_column.blockSignals(False)
        
        if hasattr(self, 'debug') and self.debug:
            print(f"Updated available measures for {group_by_dimension}")

    def update_sort_options(self):
        """
        Update the available sort options in the chart_sort_column combobox based on the selected Group By dimension.
        This ensures that appropriate sorting options are displayed for the current chart configuration.
        """
        if not hasattr(self, 'chart_data_category') or not hasattr(self, 'chart_sort_column'):
            if hasattr(self, 'debug') and self.debug:
                print("Chart UI components not found in update_sort_options")
            return
            
        group_by_dimension = self.chart_data_category.currentText()
        
        # Block signals to prevent triggering updates while updating the combobox
        self.chart_sort_column.blockSignals(True)
        
        # Clear existing items
        self.chart_sort_column.clear()
        
        # Always add the category column as a sort option
        self.chart_sort_column.addItem(group_by_dimension)
        
        # Add measure-based sort options
        if group_by_dimension == "PLAYER":
            self.chart_sort_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "CHEST":
            self.chart_sort_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "SOURCE":
            self.chart_sort_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_SCORE"])
        elif group_by_dimension == "DATE":
            self.chart_sort_column.addItems(["TOTAL_SCORE", "CHEST_COUNT", "AVG_VALUE"])
        
        # Set default sort column to the measure
        if self.chart_data_column.currentText():
            sort_column_idx = self.chart_sort_column.findText(self.chart_data_column.currentText())
            if sort_column_idx >= 0:
                self.chart_sort_column.setCurrentIndex(sort_column_idx)
        
        # Unblock signals
        self.chart_sort_column.blockSignals(False)
        
        if hasattr(self, 'debug') and self.debug:
            print(f"Updated sort options for {group_by_dimension}")

    def connect_signals(self):
        """
        Connect UI signals to their respective slots.
        
        This method connects signals for UI elements that are not connected in their 
        respective setup methods, ensuring all user interactions trigger the appropriate
        actions.
        """
        if self.debug:
            print("Connecting signals for UI elements")
        
        # ImportArea signals
        if hasattr(self, 'import_area'):
            # Disconnect first to prevent duplicate connections
            try:
                self.import_area.select_button.clicked.disconnect()
            except TypeError:
                # Signal was not connected, which is fine
                pass
            self.import_area.select_button.clicked.connect(self.import_area.open_file_dialog)
            
            try:
                self.import_area.fileSelected.disconnect()
            except TypeError:
                # Signal was not connected, which is fine
                pass
            self.import_area.fileSelected.connect(self.load_csv_file)
        
        # Menu actions
        # Create file menu if not already created
        if not hasattr(self, 'file_menu'):
            self.file_menu = self.menuBar().addMenu("&File")
            self.action_import_csv = self.file_menu.addAction("&Import CSV")
            self.action_exit = self.file_menu.addAction("E&xit")
        
        # Connect menu actions
        if hasattr(self, 'action_import_csv'):
            # Safely disconnect if connected
            try:
                self.action_import_csv.triggered.disconnect()
            except TypeError:
                # Signal was not connected, which is fine
                pass
            # Connect directly to import_area.open_file_dialog, not to open_csv_file
            if hasattr(self, 'import_area'):
                self.action_import_csv.triggered.connect(self.import_area.open_file_dialog)
        
        if hasattr(self, 'action_exit'):
            try:
                self.action_exit.triggered.disconnect()
            except TypeError:
                pass
            self.action_exit.triggered.connect(self.close)
        
        # Raw data filter signals
        if hasattr(self, 'apply_filter_button'):
            self.apply_filter_button.clicked.connect(self.apply_filter)
        if hasattr(self, 'reset_filter_button'):
            self.reset_filter_button.clicked.connect(self.reset_filter)
        if hasattr(self, 'select_all_button'):
            self.select_all_button.clicked.connect(self.select_all_values)
        if hasattr(self, 'deselect_all_button'):
            self.deselect_all_button.clicked.connect(self.deselect_all_values)
        if hasattr(self, 'column_selector'):
            self.column_selector.currentIndexChanged.connect(self.update_filter_options)
        if hasattr(self, 'show_value_selection'):
            self.show_value_selection.stateChanged.connect(self.toggle_value_selection)
        
        # Analysis filter signals
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
        
        # Export buttons
        if hasattr(self, 'export_raw_data_button'):
            self.export_raw_data_button.clicked.connect(self.export_raw_data)
        if hasattr(self, 'export_analysis_button'):
            self.export_analysis_button.clicked.connect(self.export_analysis_data)
        
        # Analysis view selector
        if hasattr(self, 'analysis_selector'):
            self.analysis_selector.currentIndexChanged.connect(self.update_analysis_view)
        
        # Chart signals
        if hasattr(self, 'chart_data_category'):
            self.chart_data_category.currentIndexChanged.connect(self.update_sort_options)
            
            # Connect chart update button if it exists
            if hasattr(self, 'chart_update_button'):
                self.chart_update_button.clicked.connect(self.update_chart)
            
            # Connect chart export button if it exists
            if hasattr(self, 'chart_export_button'):
                self.chart_export_button.clicked.connect(self.export_chart)
            elif hasattr(self, 'save_chart_button'):
                self.save_chart_button.clicked.connect(self.save_chart)
            
            # Connect all chart options to update_chart if they exist
            options_to_connect = [
                'chart_data_column', 'chart_type_selector',
                'chart_sort_column', 'chart_sort_order',
                'chart_limit_enabled', 'chart_limit_value',
                'chart_show_values', 'chart_show_grid'
            ]
            
            for option_name in options_to_connect:
                if hasattr(self, option_name):
                    option = getattr(self, option_name)
                    if isinstance(option, QComboBox):
                        option.currentIndexChanged.connect(self.update_chart)
                    elif isinstance(option, QCheckBox):
                        option.stateChanged.connect(self.update_chart)
                    elif isinstance(option, QSpinBox):
                        option.valueChanged.connect(self.update_chart)
                    
        # Report signals
        if hasattr(self, 'report_type_selector'):
            if hasattr(self, 'report_generate_button'):
                self.report_generate_button.clicked.connect(self.generate_report)
            elif hasattr(self, 'generate_report_button'):
                self.generate_report_button.clicked.connect(self.generate_report)
                
            if hasattr(self, 'report_export_button'):
                self.report_export_button.clicked.connect(self.export_report)
            elif hasattr(self, 'export_report_button'):
                self.export_report_button.clicked.connect(self.export_report)
        
        if self.debug:
            print("All signals connected")

    def open_csv_file(self):
        """Open a file dialog to select a CSV file.
        
        This method is maintained for backward compatibility with existing signal connections.
        It delegates to the ImportArea's open_file_dialog method.
        """
        if self.debug:
            print("open_csv_file called - delegating to ImportArea.open_file_dialog")
        
        # Prevent opening file dialog if one is already active
        if hasattr(self, '_file_dialog_active') and self._file_dialog_active:
            if self.debug:
                print("A file dialog is already active, ignoring duplicate call")
            return
            
        # If we have an import_area, use its method
        if hasattr(self, 'import_area'):
            self.import_area.open_file_dialog()
        else:
            if self.debug:
                print("ImportArea not available, can't open file dialog")

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

    # This is a duplicate method - removed to prevent conflicts
    # def generate_chart_for_report(self, chart_type, category_field, title):
    #     """
    #     Generate a chart image for the report.
        
    #     This helper method creates a chart image file that can be included in HTML reports.
        
    #     Args:
    #         chart_type (str): The type of chart to generate (e.g., 'Bar Chart', 'Pie Chart')
    #         category_field (str): The field to use for categorization (e.g., 'PLAYER', 'CHEST')
    #         title (str): The title of the chart
            
    #     Returns:
    #         str: The path to the generated chart image file, or None on failure
    #     """
    #     try:
    #         # Create a temporary file for the chart
    #         temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    #         temp_file.close()
            
    #         # Determine which dataset to use based on category_field
    #         if category_field == 'PLAYER':
    #             if 'player_totals' not in self.analysis_results or self.analysis_results['player_totals'].empty:
    #                 return None
    #             df = self.analysis_results['player_totals']
    #         elif category_field == 'CHEST':
    #             if 'chest_totals' not in self.analysis_results or self.analysis_results['chest_totals'].empty:
    #                 return None
    #             df = self.analysis_results['chest_totals']
    #         elif category_field == 'SOURCE':
    #             if 'source_totals' not in self.analysis_results or self.analysis_results['source_totals'].empty:
    #                 return None
    #             df = self.analysis_results['source_totals']
    #         elif category_field == 'DATE':
    #             if 'date_totals' not in self.analysis_results or self.analysis_results['date_totals'].empty:
    #                 return None
    #             df = self.analysis_results['date_totals']
    #         else:
    #             return None
            
    #         # Create the figure for the chart
    #         plt.figure(figsize=(10, 6), facecolor='#1A2742')
            
    #         # Set the style for the chart - dark background with white text
    #         plt.style.use('dark_background')
            
    #         # Get current axis
    #         ax = plt.gca()
            
    #         # Set axis colors
    #         ax.set_facecolor('#1A2742')
    #         ax.xaxis.label.set_color('#FFFFFF')
    #         ax.yaxis.label.set_color('#FFFFFF')
    #         ax.title.set_color('#D4AF37')
    #         ax.tick_params(colors='#FFFFFF')
            
    #         # Define Tableau-like colors for consistent styling
    #         TABLEAU_COLORS = [
    #             '#D4AF37',  # Gold
    #             '#5991C4',  # Blue
    #             '#6EC1A7',  # Green
    #             '#D46A5F',  # Red
    #             '#A073D1',  # Purple
    #             '#F49E5D',  # Orange
    #             '#9DC375',  # Light Green
    #             '#C4908F',  # Rose
    #             '#8595A8',  # Gray Blue
    #             '#D9A471',  # Tan
    #         ]
            
    #         # Generate the appropriate type of chart
    #         if chart_type == 'Bar Chart':
    #             if category_field == 'PLAYER':
    #                 # Use TOTAL_SCORE for players if available
    #                 score_col = 'TOTAL_SCORE' if 'TOTAL_SCORE' in df.columns else 'SCORE'
    #                 data = df.sort_values(score_col, ascending=False).head(15)  # Limit to top 15 for readability
    #                 bars = plt.bar(data['PLAYER'], data[score_col], color=TABLEAU_COLORS)
    #                 plt.xticks(rotation=45, ha='right', color='white')
    #                 plt.ylabel('Score', color='white')
    #                 plt.title('Player Total Scores', color='#D4AF37', fontsize=14)
                    
    #                 # Add values on top of bars
    #                 for bar in bars:
    #                     height = bar.get_height()
    #                     plt.text(bar.get_x() + bar.get_width()/2., height,
    #                           f'{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                    
    #             elif category_field == 'CHEST':
    #                 data = df.sort_values('SCORE', ascending=False)
    #                 bars = plt.bar(data['CHEST'], data['SCORE'], color=TABLEAU_COLORS)
    #                 plt.xticks(rotation=45, ha='right', color='white')
    #                 plt.ylabel('Score', color='white')
    #                 plt.title('Scores by Chest Type', color='#D4AF37', fontsize=14)
                    
    #                 # Add values on top of bars
    #                 for bar in bars:
    #                     height = bar.get_height()
    #                     plt.text(bar.get_x() + bar.get_width()/2., height,
    #                           f'{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                    
    #             elif category_field == 'SOURCE':
    #                 data = df.sort_values('SCORE', ascending=False)
    #                 bars = plt.bar(data['SOURCE'], data['SCORE'], color=TABLEAU_COLORS)
    #                 plt.xticks(rotation=45, ha='right', color='white')
    #                 plt.ylabel('Score', color='white')
    #                 plt.title('Scores by Source', color='#D4AF37', fontsize=14)
                    
    #                 # Add values on top of bars
    #                 for bar in bars:
    #                     height = bar.get_height()
    #                     plt.text(bar.get_x() + bar.get_width()/2., height,
    #                           f'{height:,.0f}', ha='center', va='bottom', color='white', fontweight='bold')
                    
    #             elif category_field == 'DATE':
    #                 # For dates, sort chronologically and use a line chart instead of bar
    #                 data = df.sort_values('DATE')
    #                 plt.plot(data['DATE'], data['SCORE'], marker='o', color=TABLEAU_COLORS[0], linewidth=2)
    #                 plt.xticks(rotation=45, ha='right', color='white')
    #                 plt.ylabel('Score', color='white')
    #                 plt.title('Scores by Date', color='#D4AF37', fontsize=14)
    #                 plt.grid(True, alpha=0.3, color='#3A4762')
                    
    #                 # Add values on data points
    #                 for i, value in enumerate(data['SCORE']):
    #                     plt.annotate(f'{value:,.0f}', 
    #                               (data['DATE'].iloc[i], value),
    #                               textcoords="offset points", 
    #                               xytext=(0,10), 
    #                               ha='center',
    #                               color='white',
    #                               fontweight='bold')
                
    #         elif chart_type == 'Pie Chart':
    #             if category_field == 'CHEST':
    #                 data = df.sort_values('SCORE', ascending=False)
                    
    #                 # If we have too many slices, limit to top 9 + "Others"
    #                 if len(data) > 10:
    #                     top_items = data.iloc[:9].copy()
    #                     others_sum = data.iloc[9:]['SCORE'].sum()
    #                     others_row = pd.DataFrame({
    #                         'CHEST': ['Others'],
    #                         'SCORE': [others_sum]
    #                     })
    #                     data = pd.concat([top_items, others_row]).reset_index(drop=True)
                    
    #                 # Create color list for pie slices (one color per slice)
    #                 colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                        
    #                 wedges, texts, autotexts = plt.pie(
    #                     data['SCORE'], 
    #                     labels=data['CHEST'], 
    #                     autopct='%1.1f%%', 
    #                     startangle=90, 
    #                     colors=colors,
    #                     wedgeprops={'edgecolor': temp_canvas.style_presets['default']['bg_color'], 'linewidth': 1}
    #                 )
    #                 plt.axis('equal')
    #                 plt.title('Chest Type Distribution by Score', color='#D4AF37', fontsize=14)
                    
    #                 # Make text visible on dark background
    #                 for text in texts:
    #                     text.set_color('white')
    #                 for autotext in autotexts:
    #                     autotext.set_color('white')
    #                     autotext.set_fontweight('bold')
                        
    #             elif category_field == 'SOURCE':
    #                 data = df.sort_values('SCORE', ascending=False)
                    
    #                 # If we have too many slices, limit to top 9 + "Others"
    #                 if len(data) > 10:
    #                     top_items = data.iloc[:9].copy()
    #                     others_sum = data.iloc[9:]['SCORE'].sum()
    #                     others_row = pd.DataFrame({
    #                         'SOURCE': ['Others'],
    #                         'SCORE': [others_sum]
    #                     })
    #                     data = pd.concat([top_items, others_row]).reset_index(drop=True)
                    
    #                 # Create color list for pie slices (one color per slice)
    #                 colors = [TABLEAU_COLORS[i % len(TABLEAU_COLORS)] for i in range(len(data))]
                        
    #                 wedges, texts, autotexts = plt.pie(
    #                     data['SCORE'], 
    #                     labels=data['SOURCE'], 
    #                     autopct='%1.1f%%', 
    #                     startangle=90, 
    #                     colors=colors,
    #                     wedgeprops={'edgecolor': temp_canvas.style_presets['default']['bg_color'], 'linewidth': 1}
    #                 )
    #                 plt.axis('equal')
    #                 plt.title('Source Distribution by Score', color='#D4AF37', fontsize=14)
                    
    #                 # Make text visible on dark background
    #                 for text in texts:
    #                     text.set_color('white')
    #                 for autotext in autotexts:
    #                     autotext.set_color('white')
    #                     autotext.set_fontweight('bold')
                
    #         elif chart_type == 'Stacked Bar Chart' and category_field == 'PLAYER':
    #             # Get the player and source columns
    #             player_col = 'PLAYER'
                
    #             # Get columns that represent sources (but not the special columns)
    #             data_cols = [col for col in df.columns if col not in 
    #                         ['PLAYER', 'TOTAL_SCORE', 'CHEST_COUNT', 'AVG_SCORE']]
                
    #             if data_cols:
    #                 # Sort by total score
    #                 if 'TOTAL_SCORE' in df.columns:
    #                     data = df.sort_values('TOTAL_SCORE', ascending=False).head(10)  # Limit to top 10
    #                 else:
    #                     data = df.head(10)  # Just use first 10 rows if no TOTAL_SCORE
                    
    #                 # Create the stacked bar chart
    #                 bottom = np.zeros(len(data))
    #                 for i, col in enumerate(data_cols):
    #                     if col in data.columns:
    #                         values = data[col].fillna(0).values
    #                         plt.bar(data[player_col], values, bottom=bottom, 
    #                                label=col, color=TABLEAU_COLORS[i % len(TABLEAU_COLORS)])
    #                         bottom += values
                    
    #                 plt.xticks(rotation=45, ha='right', color='white')
    #                 plt.ylabel('Score', color='white')
    #                 plt.title('Player Scores by Source', color='#D4AF37', fontsize=14)
                    
    #                 # Customize legend
    #                 legend = plt.legend(title='Source', bbox_to_anchor=(1.05, 1), loc='upper left')
    #                 legend.get_title().set_color('white')
    #                 for text in legend.get_texts():
    #                     text.set_color('white')
                    
    #                 plt.tight_layout()
            
    #         elif chart_type == 'Bubble Chart' and category_field == 'PLAYER':
    #             # Check if we have the necessary columns
    #             if 'TOTAL_SCORE' in df.columns and 'CHEST_COUNT' in df.columns:
    #                 # Filter out any rows with zeroes to avoid divide by zero
    #                 data = df[(df['TOTAL_SCORE'] > 0) & (df['CHEST_COUNT'] > 0)]
                    
    #                 if not data.empty:
    #                     # Calculate efficiency for sizing the bubbles
    #                     efficiency = data['TOTAL_SCORE'] / data['CHEST_COUNT']
                        
    #                     # Calculate sizes proportional to efficiency
    #                     max_size = 1000
    #                     min_size = 100
    #                     if efficiency.max() > efficiency.min():
    #                         size_scale = ((efficiency - efficiency.min()) / 
    #                                      (efficiency.max() - efficiency.min())) * (max_size - min_size) + min_size
    #                     else:
    #                         size_scale = np.ones(len(efficiency)) * max_size
                        
    #                     # Create the bubble chart
    #                     scatter = plt.scatter(data['CHEST_COUNT'], data['TOTAL_SCORE'], 
    #                                         s=size_scale, alpha=0.6, 
    #                                         c=range(len(data)), cmap='viridis')
                        
    #                     # Add player labels
    #                     for i, player in enumerate(data['PLAYER']):
    #                         plt.annotate(player, 
    #                                     (data['CHEST_COUNT'].iloc[i], data['TOTAL_SCORE'].iloc[i]),
    #                                     xytext=(5, 5), textcoords='offset points',
    #                                     color='white', fontweight='bold')
                        
    #                     plt.xlabel('Chest Count', color='white')
    #                     plt.ylabel('Total Score', color='white')
    #                     plt.title('Player Efficiency (Score vs Chest Count)', color='#D4AF37', fontsize=14)
                        
    #                     # Add a colorbar to show efficiency
    #                     colorbar = plt.colorbar(scatter)
    #                     colorbar.set_label('Efficiency (pts/chest)', color='white')
    #                     colorbar.ax.yaxis.set_tick_params(color='white')
    #                     plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
            
    #         # Set spine colors to match theme
    #         for spine in ax.spines.values():
    #             spine.set_color('#3A4762')
            
    #         # Setup grid
    #         ax.grid(True, color='#3A4762', linestyle='--', alpha=0.3)
            
    #         # Adjust layout and save with transparent background
    #         plt.tight_layout()
    #         plt.savefig(temp_file.name, format='png', dpi=150, bbox_inches='tight', 
    #                   facecolor='#1A2742', edgecolor='none')
    #         plt.close()
            
    #         return temp_file.name
            
    #     except Exception as e:
    #         print(f"Error generating chart for report: {e}")
    #         traceback.print_exc()
    #         return None

    def generate_report(self):
        """
        Generate a report based on user selections and display it in the report view.
        
        This method creates an HTML report based on the selected report type and
        inclusion options (charts, tables, statistics). The report is displayed
        in the report_view component and can be exported using the export_report method.
        """
        try:
            # Check if we have analysis results
            if not hasattr(self, 'analysis_results') or not self.analysis_results:
                QMessageBox.warning(self, "Report Generation Error", 
                                   "No analysis results available. Please import and analyze data first.")
                return
                
            # Get report type and inclusion options
            report_type = self.report_type_selector.currentText()
            include_charts = self.include_charts_checkbox.isChecked()
            include_tables = self.include_tables_checkbox.isChecked()
            include_stats = self.include_stats_checkbox.isChecked()
            
            # Update status
            self.statusBar().showMessage(f"Generating {report_type}...")
            
            # Colors from the dark theme
            background_color = '#0E1629'    # Dark blue background
            text_color = '#FFFFFF'          # White text
            accent_color = '#D4AF37'        # Gold accent
            border_color = '#2A3F5F'        # Border color
            bg_light = '#1A2742'            # Lighter background
            
            # Generate HTML content based on report type
            if report_type == "Full Report":
                html_content = self.create_full_report_html(include_charts, include_tables, include_stats)
            elif report_type == "Player Performance":
                html_content = self.create_player_performance_html(include_charts, include_tables, include_stats)
            elif report_type == "Chest Type Analysis":
                html_content = self.create_chest_analysis_html(include_charts, include_tables, include_stats)
            elif report_type == "Source Analysis":
                html_content = self.create_source_analysis_html(include_charts, include_tables, include_stats)
            else:
                html_content = "<h1>Invalid report type selected</h1>"
                
            # Ensure the HTML content has proper styling with background color
            if "<!DOCTYPE html>" not in html_content:
                # Add proper HTML structure with styling if not already present
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Total Battle Analyzer - {report_type}</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: {background_color};
                            color: {text_color};
                            margin: 20px;
                        }}
                        h1, h2, h3, h4 {{
                            color: {accent_color};
                        }}
                        .header {{
                            border-bottom: 2px solid {accent_color};
                            padding-bottom: 10px;
                            margin-bottom: 20px;
                        }}
                        .section {{
                            margin-bottom: 30px;
                            background-color: {bg_light};
                            padding: 15px;
                            border-radius: 5px;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 15px 0;
                        }}
                        th, td {{
                            border: 1px solid {border_color};
                            padding: 8px;
                            text-align: left;
                        }}
                        th {{
                            background-color: {background_color};
                            color: {accent_color};
                        }}
                        .chart-container {{
                            margin: 20px 0;
                            text-align: center;
                        }}
                        .footer {{
                            margin-top: 30px;
                            text-align: center;
                            font-size: 0.8em;
                            color: {text_color};
                            border-top: 1px solid {border_color};
                            padding-top: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Total Battle Analyzer - {report_type}</h1>
                        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    {html_content}
                    <div class="footer">
                        <p>Total Battle Analyzer - Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </body>
                </html>
                """
                
            # Display the report in the report view
            self.report_view.setHtml(html_content)
            
            # Update status
            self.statusBar().showMessage(f"{report_type} generated successfully.", 5000)
            
        except Exception as e:
            log_error("Error generating report", e)
            QMessageBox.critical(self, "Report Generation Error", 
                               f"An error occurred during report generation: {str(e)}")
            self.statusBar().showMessage("Error generating report.", 5000)

    def create_player_performance_html(self, include_charts=True, include_tables=True, include_stats=True):
        """
        Create HTML content for the Player Performance report.
        
        Args:
            include_charts (bool): Whether to include charts in the report
            include_tables (bool): Whether to include tables in the report
            include_stats (bool): Whether to include statistics in the report
            
        Returns:
            str: HTML content for the report
        """
        # Get current date and time for the report header
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Colors from the dark theme
        background_color = '#0E1629'    # Dark blue background
        text_color = '#FFFFFF'          # White text
        accent_color = '#D4AF37'        # Gold accent
        border_color = '#2A3F5F'        # Border color
        bg_light = '#1A2742'            # Lighter background

        # Start with the HTML header and styling
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Total Battle Analyzer - Player Performance</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: {background_color};
                    color: {text_color};
                    margin: 20px;
                }}
                h1, h2, h3, h4 {{
                    color: {accent_color};
                }}
                .header {{
                    border-bottom: 2px solid {accent_color};
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .section {{
                    margin-bottom: 30px;
                    background-color: {bg_light};
                    padding: 15px;
                    border-radius: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    border: 1px solid {border_color};
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: {background_color};
                    color: {accent_color};
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.8em;
                    color: {text_color};
                    border-top: 1px solid {border_color};
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Total Battle Analyzer - Player Performance</h1>
                <p>Generated on: {current_datetime}</p>
            </div>
        """

        # Player Overview Section
        html += """
        <div class="section">
            <h2>Player Overview</h2>
        """

        if include_stats and 'player_totals' in self.analysis_results:
            # Add player statistics
            player_df = self.analysis_results['player_totals']
            if not player_df.empty:
                # Use 'SCORE' instead of 'TOTAL_SCORE' for player_totals
                top_player = player_df.sort_values('SCORE', ascending=False).iloc[0]
                total_players = len(player_df)
                avg_score = player_df['SCORE'].mean()
                
                html += f"""
                <p>Total Players: {total_players}</p>
                <p>Average Score per Player: {avg_score:.2f}</p>
                <p>Top Player: {top_player['PLAYER']} with {top_player['SCORE']:.2f} points</p>
                """
            else:
                html += "<p>No player data available for statistics</p>"
                
        html += "</div>"  # End of Player Overview section
        
        # Player Performance Details Section
        html += """
        <div class="section">
            <h2>Player Performance Details</h2>
        """

        if include_charts and 'player_totals' in self.analysis_results:
            # Generate bar chart for player performance
            bar_chart_file = self.generate_chart_for_report('Bar Chart', 'PLAYER', 'Player Total Scores')
            if bar_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{bar_chart_file}" alt="Player Performance Chart" style="max-width:100%; height:auto;">
                    <p>Player Total Scores</p>
                </div>
                """
            
            # Generate bubble chart for player efficiency if we have the necessary data
            player_df = self.analysis_results['player_totals']
            if not player_df.empty and 'CHEST_COUNT' in player_df.columns and 'TOTAL_SCORE' in player_df.columns:
                bubble_chart_file = self.generate_chart_for_report('Bubble Chart', 'PLAYER', 'Player Efficiency')
                if bubble_chart_file:
                    html += f"""
                    <div class="chart-container">
                        <img src="file:///{bubble_chart_file}" alt="Player Efficiency Chart" style="max-width:100%; height:auto;">
                        <p>Player Efficiency (Score vs Chest Count)</p>
                    </div>
                    """
            
            # Generate stacked bar chart for player source breakdown
            stacked_chart_file = self.generate_chart_for_report('Stacked Bar Chart', 'PLAYER', 'Player Overview')
            if stacked_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{stacked_chart_file}" alt="Player Source Breakdown" style="max-width:100%; height:auto;">
                    <p>Player Scores by Source</p>
                </div>
                """
            
            if not bar_chart_file and (not 'bubble_chart_file' in locals() or not bubble_chart_file) and (not 'stacked_chart_file' in locals() or not stacked_chart_file):
                html += """
                <div class="chart-container">
                    <p>[Could not generate Player Performance Charts]</p>
                </div>
                """
            
        if include_tables and 'player_totals' in self.analysis_results:
            # Add player performance table
            player_df = self.analysis_results['player_totals']
            if not player_df.empty:
                # Convert DataFrame to HTML table
                player_table = player_df.to_html(index=False, classes="table")
                html += f"""
                <h3>Player Performance Data</h3>
                {player_table}
                """
            else:
                html += "<p>No player performance data available</p>"
                
        html += "</div>"  # End of Player Performance Details section
        
        # Player Efficiency Section
        html += """
        <div class="section">
            <h2>Player Efficiency Analysis</h2>
        """

        if include_stats and 'player_totals' in self.analysis_results:
            # Add player efficiency statistics
            player_df = self.analysis_results['player_totals']
            if not player_df.empty and 'CHEST_COUNT' in player_df.columns and 'TOTAL_SCORE' in player_df.columns:
                # Calculate points per chest for each player
                player_df['POINTS_PER_CHEST'] = player_df['TOTAL_SCORE'] / player_df['CHEST_COUNT'].replace(0, 1)
                most_efficient_player = player_df.sort_values('POINTS_PER_CHEST', ascending=False).iloc[0]
                
                html += f"""
                <p>Most Efficient Player: {most_efficient_player['PLAYER']} with {most_efficient_player['POINTS_PER_CHEST']:.2f} points per chest</p>
                """
                
                # Show top 5 most efficient players
                top_5_efficient = player_df.sort_values('POINTS_PER_CHEST', ascending=False).head(5)
                efficient_table = top_5_efficient[['PLAYER', 'POINTS_PER_CHEST', 'TOTAL_SCORE', 'CHEST_COUNT']].to_html(index=False, classes="table")
                
                html += f"""
                <h3>Top 5 Most Efficient Players</h3>
                {efficient_table}
                """
            else:
                html += "<p>No player efficiency data available</p>"
                
        html += "</div>"  # End of Player Efficiency section
        
        # Footer
        html += f"""
        <div class="footer">
            <p>Total Battle Analyzer - Player Performance Report generated on {current_datetime}</p>
        </div>
        </body>
        </html>
        """

        return html

    def create_full_report_html(self, include_charts, include_tables, include_stats):
        """
        Create HTML content for the Full Report type.
        
        Args:
            include_charts (bool): Whether to include charts in the report
            include_tables (bool): Whether to include tables in the report
            include_stats (bool): Whether to include statistics in the report
            
        Returns:
            str: HTML content for the report
        """
        # Get current date and time for the report header
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Colors from the dark theme
        background_color = '#0E1629'    # Dark blue background
        text_color = '#FFFFFF'          # White text
        accent_color = '#D4AF37'        # Gold accent
        border_color = '#2A3F5F'        # Border color
        bg_light = '#1A2742'            # Lighter background

        # Start with the HTML header and styling
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Total Battle Analyzer - Full Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: {background_color};
                    color: {text_color};
                    margin: 20px;
                }}
                h1, h2, h3, h4 {{
                    color: {accent_color};
                }}
                .header {{
                    border-bottom: 2px solid {accent_color};
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .section {{
                    margin-bottom: 30px;
                    background-color: {bg_light};
                    padding: 15px;
                    border-radius: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    border: 1px solid {border_color};
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: {background_color};
                    color: {accent_color};
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.8em;
                    color: {text_color};
                    border-top: 1px solid {border_color};
                    padding-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Total Battle Analyzer - Full Report</h1>
                <p>Generated on: {current_datetime}</p>
            </div>
        """

        # Overview Section
        html += """
        <div class="section">
            <h2>Overview</h2>
        """
        
        if include_stats and 'player_totals' in self.analysis_results and 'chest_totals' in self.analysis_results:
            player_df = self.analysis_results['player_totals']
            chest_df = self.analysis_results['chest_totals']
            
            if not player_df.empty and not chest_df.empty:
                total_players = len(player_df)
                total_chest_types = len(chest_df)
                total_score = player_df['SCORE'].sum() if 'SCORE' in player_df.columns else 0
                total_chests = chest_df['CHEST_COUNT'].sum() if 'CHEST_COUNT' in chest_df.columns else 0
                
                html += f"""
                <p>Total Players: {total_players}</p>
                <p>Total Chest Types: {total_chest_types}</p>
                <p>Total Score: {total_score:,.0f}</p>
                <p>Total Chests: {total_chests:,.0f}</p>
                """
            else:
                html += "<p>No overview data available</p>"
                
        html += "</div>"  # End of Overview section
        
        # Player Performance Section
        html += """
        <div class="section">
            <h2>Player Performance</h2>
        """

        if include_charts and 'player_totals' in self.analysis_results:
            # Generate bar chart for player performance
            bar_chart_file = self.generate_chart_for_report('Bar Chart', 'PLAYER', 'Player Total Scores')
            if bar_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{bar_chart_file}" alt="Player Performance Chart" style="max-width:100%; height:auto;">
                    <p>Player Total Scores</p>
                </div>
                """
        
        if include_tables and 'player_totals' in self.analysis_results:
            # Add player performance table
            player_df = self.analysis_results['player_totals']
            if not player_df.empty:
                # Sort by score descending
                player_df = player_df.sort_values('SCORE', ascending=False)
                # Convert DataFrame to HTML table
                player_table = player_df.to_html(index=False, classes="table")
                html += f"""
                <h3>Player Performance Data</h3>
                {player_table}
                """
            else:
                html += "<p>No player performance data available</p>"
                
        html += "</div>"  # End of Player Performance section
        
        # Chest Analysis Section
        html += """
        <div class="section">
            <h2>Chest Analysis</h2>
        """

        if include_charts and 'chest_totals' in self.analysis_results:
            # Generate pie chart for chest distribution
            pie_chart_file = self.generate_chart_for_report('Pie Chart', 'CHEST', 'Chest Score Distribution')
            if pie_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{pie_chart_file}" alt="Chest Distribution Chart" style="max-width:100%; height:auto;">
                    <p>Chest Score Distribution</p>
                </div>
                """
                
            # Generate bar chart for chest scores
            bar_chart_file = self.generate_chart_for_report('Bar Chart', 'CHEST', 'Chest Scores')
            if bar_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{bar_chart_file}" alt="Chest Scores Chart" style="max-width:100%; height:auto;">
                    <p>Chest Scores by Type</p>
                </div>
                """
        
        if include_tables and 'chest_totals' in self.analysis_results:
            # Add chest analysis table
            chest_df = self.analysis_results['chest_totals']
            if not chest_df.empty:
                # Sort by score descending
                chest_df = chest_df.sort_values('SCORE', ascending=False)
                # Convert DataFrame to HTML table
                chest_table = chest_df.to_html(index=False, classes="table")
                html += f"""
                <h3>Chest Analysis Data</h3>
                {chest_table}
                """
            else:
                html += "<p>No chest analysis data available</p>"
                
        html += "</div>"  # End of Chest Analysis section
        
        # Source Analysis Section
        html += """
        <div class="section">
            <h2>Source Analysis</h2>
        """

        if include_charts and 'source_totals' in self.analysis_results:
            # Generate pie chart for source distribution
            pie_chart_file = self.generate_chart_for_report('Pie Chart', 'SOURCE', 'Source Score Distribution')
            if pie_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{pie_chart_file}" alt="Source Distribution Chart" style="max-width:100%; height:auto;">
                    <p>Source Score Distribution</p>
                </div>
                """
                
            # Generate bar chart for source scores
            bar_chart_file = self.generate_chart_for_report('Bar Chart', 'SOURCE', 'Source Scores')
            if bar_chart_file:
                html += f"""
                <div class="chart-container">
                    <img src="file:///{bar_chart_file}" alt="Source Scores Chart" style="max-width:100%; height:auto;">
                    <p>Source Scores by Type</p>
                </div>
                """
        
        if include_tables and 'source_totals' in self.analysis_results:
            # Add source analysis table
            source_df = self.analysis_results['source_totals']
            if not source_df.empty:
                # Sort by score descending
                source_df = source_df.sort_values('SCORE', ascending=False)
                # Convert DataFrame to HTML table
                source_table = source_df.to_html(index=False, classes="table")
                html += f"""
                <h3>Source Analysis Data</h3>
                {source_table}
                """
            else:
                html += "<p>No source analysis data available</p>"
                
        html += "</div>"  # End of Source Analysis section
        
        # Footer
        html += f"""
        <div class="footer">
            <p>Total Battle Analyzer - Full Report generated on {current_datetime}</p>
        </div>
        </body>
        </html>
        """

        return html

    def export_report(self):
        """
        Export the currently displayed report to HTML or PDF.
        
        This method allows the user to save the current report as an HTML or
        PDF file for sharing or future reference.
        """
        try:
            # Check if there is a report to export
            if not self.report_view.toHtml():
                QMessageBox.warning(self, "Export Error", "No report to export. Please generate a report first.")
                return

            # Get report type
            report_type = self.report_type_selector.currentText()

            # Create a suggested filename based on the report type
            filename_safe_report_type = report_type.replace(" ", "_")
            suggested_filename = f"TotalBattle_{filename_safe_report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Get the export directory from config
            export_dir = Path(self.config_manager.get_export_directory())
            if not export_dir.exists():
                export_dir.mkdir(parents=True, exist_ok=True)

            # Show file dialog to select export format and location
            export_options = "HTML Files (*.html);;PDF Files (*.pdf)"
            filepath, selected_filter = QFileDialog.getSaveFileName(
                self, "Export Report", str(export_dir / suggested_filename), export_options
            )

            if not filepath:
                return

            # Save the current directory for next time
            self.config_manager.set_export_directory(str(Path(filepath).parent))

            if selected_filter == "HTML Files (*.html)":
                # Export as HTML
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.report_view.toHtml())
                    
                self.statusBar().showMessage(f"Report exported as HTML: {filepath}", 5000)
            
            elif selected_filter == "PDF Files (*.pdf)":
                # Export as PDF
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filepath)
                self.report_view.print_(printer)
                
                self.statusBar().showMessage(f"Report exported as PDF: {filepath}", 5000)
            
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filepath}")
            
        except Exception as e:
            log_error("Error exporting report", e)
            QMessageBox.warning(self, "Export Error", f"An error occurred while exporting the report: {str(e)}")
            self.statusBar().showMessage("Error exporting report", 5000)

    def create_chest_analysis_html(self, include_charts=True, include_tables=True, include_stats=True):
        """
        Generate HTML content for chest analysis report.
        
        Args:
            include_charts (bool): Whether to include charts in the report
            include_tables (bool): Whether to include tables in the report
            include_stats (bool): Whether to include statistics in the report
            
        Returns:
            str: HTML content for the chest analysis report
        """
        # Colors
        background_color = '#0E1629'    # Dark blue background
        text_color = '#FFFFFF'          # White text
        accent_color = '#D4AF37'        # Gold accent
        border_color = '#2A3F5F'        # Border color
        bg_light = '#1A2742'            # Lighter background
        
        # Initial HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Chest Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: {background_color};
                    color: {text_color};
                    padding: 20px;
                    margin: 0;
                }}
                h1, h2, h3 {{
                    color: {accent_color};
                }}
                h1 {{
                    border-bottom: 2px solid {accent_color};
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background-color: {bg_light};
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid {border_color};
                }}
                th {{
                    background-color: {bg_light};
                    color: {accent_color};
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: rgba(42, 63, 95, 0.5);
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid {border_color};
                    background-color: {bg_light};
                    padding: 10px;
                }}
                .stats-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background-color: {bg_light};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    width: calc(33% - 20px);
                    box-sizing: border-box;
                    text-align: center;
                }}
                .stat-box p {{
                    margin: 5px 0;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {accent_color};
                }}
                .report-section {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: {bg_light};
                    border-radius: 5px;
                    border: 1px solid {border_color};
                }}
            </style>
        </head>
        <body>
            <h1>Chest Analysis Report</h1>
            <p>This report provides an analysis of chest types in Total Battle, including their distribution and value.</p>
        """
        
        # Check if we have analysis results
        if not self.analysis_results or 'chest_totals' not in self.analysis_results:
            html += "<p>No chest analysis data available. Please import and analyze data first.</p>"
            html += "</body></html>"
            return html
            
        # Get chest totals data
        chest_data = self.analysis_results['chest_totals']
        
        # Charts Section
        if include_charts:
            html += """
            <div class="report-section">
                <h2>Charts</h2>
            """
            
            # Chest by Score Bar Chart
            if chest_data is not None and not chest_data.empty:
                chart_path = self.generate_chart_for_report("bar", "CHEST", "Chest Score Distribution")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Chest Score Distribution</h3>
                        <img src="file:///{chart_path}" alt="Chest Score Distribution">
                    </div>
                    """
                    
                # Chest by Count Bar Chart
                chart_path = self.generate_chart_for_report("bar", "CHEST", "Chest Count Distribution")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Chest Count Distribution</h3>
                        <img src="file:///{chart_path}" alt="Chest Count Distribution">
                    </div>
                    """
                    
                # Chest Score Pie Chart
                chart_path = self.generate_chart_for_report("pie", "CHEST", "Chest Score Proportion")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Chest Score Proportion</h3>
                        <img src="file:///{chart_path}" alt="Chest Score Proportion">
                    </div>
                    """
            else:
                html += "<p>No chest data available for charts.</p>"
                
            html += "</div>"  # End of charts section
        
        # Statistics Section
        if include_stats:
            html += """
            <div class="report-section">
                <h2>Key Statistics</h2>
            """
            
            if chest_data is not None and not chest_data.empty:
                try:
                    # Get stats for the section
                    chest_types = len(chest_data)
                    total_score = chest_data['SCORE'].sum()
                    avg_score = chest_data['SCORE'].mean()
                    max_score = chest_data['SCORE'].max()
                    top_chest = chest_data.loc[chest_data['SCORE'].idxmax(), 'CHEST']
                    total_chests = chest_data['CHEST_COUNT'].sum()
                    
                    html += f"""
                    <div class="stats-container">
                        <div class="stat-box">
                            <p>Total Chest Types</p>
                            <p class="stat-value">{chest_types}</p>
                        </div>
                        <div class="stat-box">
                            <p>Total Score from Chests</p>
                            <p class="stat-value">{total_score:,.0f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Average Score per Chest Type</p>
                            <p class="stat-value">{avg_score:,.1f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Highest Scoring Chest</p>
                            <p class="stat-value">{top_chest}</p>
                        </div>
                        <div class="stat-box">
                            <p>Highest Score Value</p>
                            <p class="stat-value">{max_score:,.0f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Total Number of Chests</p>
                            <p class="stat-value">{total_chests:,.0f}</p>
                        </div>
                    </div>
                    """
                except Exception as e:
                    html += f"<p>Error generating statistics: {str(e)}</p>"
            else:
                html += "<p>No chest data available for statistics.</p>"
                
            html += "</div>"  # End of statistics section
        
        # Table Section
        if include_tables:
            html += """
            <div class="report-section">
                <h2>Chest Data Table</h2>
            """
            
            if chest_data is not None and not chest_data.empty:
                # Sort by score descending
                chest_data = chest_data.sort_values('SCORE', ascending=False)
                
                # Convert DataFrame to HTML table
                table_html = chest_data.to_html(index=False)
                
                # Improve table styling
                table_html = table_html.replace('<table', '<table class="data-table"')
                
                html += table_html
            else:
                html += "<p>No chest data available for table display.</p>"
                
            html += "</div>"  # End of table section
            
        # Close HTML
        html += "</body></html>"
        
        return html
        
    def create_source_analysis_html(self, include_charts=True, include_tables=True, include_stats=True):
        """
        Generate HTML content for source analysis report.
        
        Args:
            include_charts (bool): Whether to include charts in the report
            include_tables (bool): Whether to include tables in the report
            include_stats (bool): Whether to include statistics in the report
            
        Returns:
            str: HTML content for the source analysis report
        """
        # Colors
        background_color = '#0E1629'    # Dark blue background
        text_color = '#FFFFFF'          # White text
        accent_color = '#D4AF37'        # Gold accent
        border_color = '#2A3F5F'        # Border color
        bg_light = '#1A2742'            # Lighter background
        
        # Initial HTML structure
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Source Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: {background_color};
                    color: {text_color};
                    padding: 20px;
                    margin: 0;
                }}
                h1, h2, h3 {{
                    color: {accent_color};
                }}
                h1 {{
                    border-bottom: 2px solid {accent_color};
                    padding-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background-color: {bg_light};
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid {border_color};
                }}
                th {{
                    background-color: {bg_light};
                    color: {accent_color};
                    font-weight: bold;
                }}
                tr:hover {{
                    background-color: rgba(42, 63, 95, 0.5);
                }}
                .chart-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid {border_color};
                    background-color: {bg_light};
                    padding: 10px;
                }}
                .stats-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: space-between;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background-color: {bg_light};
                    border: 1px solid {border_color};
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    width: calc(33% - 20px);
                    box-sizing: border-box;
                    text-align: center;
                }}
                .stat-box p {{
                    margin: 5px 0;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {accent_color};
                }}
                .report-section {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: {bg_light};
                    border-radius: 5px;
                    border: 1px solid {border_color};
                }}
            </style>
        </head>
        <body>
            <h1>Source Analysis Report</h1>
            <p>This report provides an analysis of chest sources in Total Battle, including their distribution and value.</p>
        """
        
        # Check if we have analysis results
        if not self.analysis_results or 'source_totals' not in self.analysis_results:
            html += "<p>No source analysis data available. Please import and analyze data first.</p>"
            html += "</body></html>"
            return html
            
        # Get source totals data
        source_data = self.analysis_results['source_totals']
        
        # Charts Section
        if include_charts:
            html += """
            <div class="report-section">
                <h2>Charts</h2>
            """
            
            # Source by Score Bar Chart
            if source_data is not None and not source_data.empty:
                chart_path = self.generate_chart_for_report("bar", "SOURCE", "Source Score Distribution")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Source Score Distribution</h3>
                        <img src="file:///{chart_path}" alt="Source Score Distribution">
                    </div>
                    """
                    
                # Source by Count Bar Chart
                chart_path = self.generate_chart_for_report("bar", "SOURCE", "Source Count Distribution")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Source Count Distribution</h3>
                        <img src="file:///{chart_path}" alt="Source Count Distribution">
                    </div>
                    """
                    
                # Source Score Pie Chart
                chart_path = self.generate_chart_for_report("pie", "SOURCE", "Source Score Proportion")
                if chart_path:
                    html += f"""
                    <div class="chart-container">
                        <h3>Source Score Proportion</h3>
                        <img src="file:///{chart_path}" alt="Source Score Proportion">
                    </div>
                    """
            else:
                html += "<p>No source data available for charts.</p>"
                
            html += "</div>"  # End of charts section
        
        # Statistics Section
        if include_stats:
            html += """
            <div class="report-section">
                <h2>Key Statistics</h2>
            """
            
            if source_data is not None and not source_data.empty:
                try:
                    # Get stats for the section
                    source_types = len(source_data)
                    total_score = source_data['SCORE'].sum()
                    avg_score = source_data['SCORE'].mean()
                    max_score = source_data['SCORE'].max()
                    top_source = source_data.loc[source_data['SCORE'].idxmax(), 'SOURCE']
                    total_chests = source_data['CHEST_COUNT'].sum()
                    
                    html += f"""
                    <div class="stats-container">
                        <div class="stat-box">
                            <p>Total Source Types</p>
                            <p class="stat-value">{source_types}</p>
                        </div>
                        <div class="stat-box">
                            <p>Total Score from Sources</p>
                            <p class="stat-value">{total_score:,.0f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Average Score per Source</p>
                            <p class="stat-value">{avg_score:,.1f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Highest Scoring Source</p>
                            <p class="stat-value">{top_source}</p>
                        </div>
                        <div class="stat-box">
                            <p>Highest Score Value</p>
                            <p class="stat-value">{max_score:,.0f}</p>
                        </div>
                        <div class="stat-box">
                            <p>Total Number of Chests</p>
                            <p class="stat-value">{total_chests:,.0f}</p>
                        </div>
                    </div>
                    """
                except Exception as e:
                    html += f"<p>Error generating statistics: {str(e)}</p>"
            else:
                html += "<p>No source data available for statistics.</p>"
                
            html += "</div>"  # End of statistics section
        
        # Table Section
        if include_tables:
            html += """
            <div class="report-section">
                <h2>Source Data Table</h2>
            """
            
            if source_data is not None and not source_data.empty:
                # Sort by score descending
                source_data = source_data.sort_values('SCORE', ascending=False)
                
                # Convert DataFrame to HTML table
                table_html = source_data.to_html(index=False)
                
                # Improve table styling
                table_html = table_html.replace('<table', '<table class="data-table"')
                
                html += table_html
            else:
                html += "<p>No source data available for table display.</p>"
                
            html += "</div>"  # End of table section
            
        # Close HTML
        html += "</body></html>"
        
        return html
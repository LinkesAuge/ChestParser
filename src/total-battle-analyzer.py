import sys
import os
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
# Configure matplotlib to use PySide6
import matplotlib
matplotlib.use('QtAgg')  # Use the generic Qt backend that works with PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QPushButton, QTabWidget, QLabel, QFileDialog,
    QComboBox, QGroupBox, QSplitter, QMessageBox, QFrame, QHeaderView
)
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, Signal, QMimeData, 
    QUrl, QSize, Slot, QSortFilterProxyModel
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QDropEvent, QDragEnterEvent,
    QColor, QPalette, QFont, QIcon, QPixmap
)

# Style constants
DARK_THEME = {
    'background': '#2D2D30',
    'foreground': '#CCCCCC',
    'accent': '#3C7B8C',
    'accent_hover': '#4C8B9C',
    'secondary': '#6C567B',
    'success': '#56A64B',
    'error': '#A6564B',
    'card_bg': '#252526',
    'border': '#3F3F46',
    'text_disabled': '#666666'
}

class StyleManager:
    @staticmethod
    def apply_dark_theme(app):
        """Apply dark theme to the entire application"""
        dark_palette = QPalette()
        
        # Set colors
        dark_palette.setColor(QPalette.Window, QColor(DARK_THEME['background']))
        dark_palette.setColor(QPalette.WindowText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Base, QColor(DARK_THEME['card_bg']))
        dark_palette.setColor(QPalette.AlternateBase, QColor(DARK_THEME['background']))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.ToolTipText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Text, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.Button, QColor(DARK_THEME['background']))
        dark_palette.setColor(QPalette.ButtonText, QColor(DARK_THEME['foreground']))
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(DARK_THEME['accent']))
        dark_palette.setColor(QPalette.Highlight, QColor(DARK_THEME['accent']))
        dark_palette.setColor(QPalette.HighlightedText, QColor(DARK_THEME['foreground']))
        
        app.setPalette(dark_palette)
        
        # Set stylesheet for detailed styling
        app.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
            }}
            QTabWidget::pane {{
                border: 1px solid {DARK_THEME['border']};
                background-color: {DARK_THEME['card_bg']};
            }}
            QTabBar::tab {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
                padding: 8px 16px;
                border: 1px solid {DARK_THEME['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {DARK_THEME['card_bg']};
                border-bottom: 2px solid {DARK_THEME['accent']};
            }}
            QPushButton {{
                background-color: {DARK_THEME['accent']};
                color: {DARK_THEME['foreground']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {DARK_THEME['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['text_disabled']};
            }}
            QTableView {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                gridline-color: {DARK_THEME['border']};
                border: 1px solid {DARK_THEME['border']};
                border-radius: 4px;
                selection-background-color: {DARK_THEME['accent']};
            }}
            QHeaderView::section {{
                background-color: {DARK_THEME['background']};
                color: {DARK_THEME['foreground']};
                padding: 6px;
                border: 1px solid {DARK_THEME['border']};
            }}
            QComboBox {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                border: 1px solid {DARK_THEME['border']};
                padding: 6px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {DARK_THEME['card_bg']};
                color: {DARK_THEME['foreground']};
                selection-background-color: {DARK_THEME['accent']};
            }}
            QLabel {{
                color: {DARK_THEME['foreground']};
            }}
            QGroupBox {{
                border: 1px solid {DARK_THEME['border']};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {DARK_THEME['foreground']};
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
    """Matplotlib canvas for embedding in Qt"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.fig.patch.set_facecolor(DARK_THEME['card_bg'])
        
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor(DARK_THEME['card_bg'])
        self.axes.tick_params(colors=DARK_THEME['foreground'])
        self.axes.spines['bottom'].set_color(DARK_THEME['border'])
        self.axes.spines['top'].set_color(DARK_THEME['border'])
        self.axes.spines['left'].set_color(DARK_THEME['border'])
        self.axes.spines['right'].set_color(DARK_THEME['border'])
        
        super().__init__(self.fig)
        self.setParent(parent)

class DropArea(QWidget):
    """Custom widget for handling file drops"""
    
    fileDropped = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Enable drop acceptance
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Drop CSV file here")
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        
        self.description = QLabel("or click to select a file")
        self.description.setAlignment(Qt.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(self.description)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMinimumHeight(200)
        
        # Style the drop area
        self.setStyleSheet(f"""
            DropArea {{
                border: 2px dashed {DARK_THEME['border']};
                border-radius: 8px;
                background-color: {DARK_THEME['card_bg']};
            }}
            DropArea:hover {{
                border-color: {DARK_THEME['accent']};
            }}
        """)
    
    def mousePressEvent(self, event):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if filepath:
            self.fileDropped.emit(filepath)
    
    # Override all drag and drop events with simplified but robust implementations
    def dragEnterEvent(self, event):
        print(f"DropArea: dragEnterEvent - mimeData formats: {event.mimeData().formats()}")
        
        # Accept any kind of drag to start with for better user experience
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            print(f"DropArea: dragEnterEvent - URLs: {[url.toString() for url in urls]}")
            
            # Check if any of the URLs are CSV files
            has_csv = False
            for url in urls:
                filepath = url.toLocalFile()
                print(f"DropArea: dragEnterEvent - Checking file: {filepath}")
                if filepath.lower().endswith('.csv'):
                    has_csv = True
                    break
                    
            if has_csv:
                print("DropArea: dragEnterEvent - Found CSV file, accepting")
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                    DropArea {{
                        border: 2px dashed {DARK_THEME['accent']};
                        border-radius: 8px;
                        background-color: {DARK_THEME['card_bg']};
                    }}
                """)
            else:
                print("DropArea: dragEnterEvent - No CSV files found, ignoring")
                event.ignore()
        else:
            print("DropArea: dragEnterEvent - No URLs in mimeData, ignoring")
            event.ignore()
        
    def dragMoveEvent(self, event):
        print("DropArea: dragMoveEvent")
        # Accept move event if it has URLs with CSV files
        if event.mimeData().hasUrls():
            has_csv = False
            for url in event.mimeData().urls():
                filepath = url.toLocalFile()
                if filepath.lower().endswith('.csv'):
                    has_csv = True
                    break
            
            if has_csv:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
        
    def dragLeaveEvent(self, event):
        print("DropArea: dragLeaveEvent")
        event.accept()
        # Reset the style when drag leaves
        self.setStyleSheet(f"""
            DropArea {{
                border: 2px dashed {DARK_THEME['border']};
                border-radius: 8px;
                background-color: {DARK_THEME['card_bg']};
            }}
            DropArea:hover {{
                border-color: {DARK_THEME['accent']};
            }}
        """)
    
    def dropEvent(self, event):
        print(f"DropArea: dropEvent - mimeData formats: {event.mimeData().formats()}")
        
        # Process mimeData to extract file paths
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            print(f"DropArea: dropEvent - URLs: {[url.toString() for url in urls]}")
            
            for url in urls:
                filepath = url.toLocalFile()
                print(f"DropArea: dropEvent - Processing file: {filepath}")
                
                # Only process CSV files
                if filepath.lower().endswith('.csv'):
                    print(f"DropArea: dropEvent - Found CSV file: {filepath}")
                    event.acceptProposedAction()
                    
                    # Reset style after successful drop
                    self.setStyleSheet(f"""
                        DropArea {{
                            border: 2px dashed {DARK_THEME['border']};
                            border-radius: 8px;
                            background-color: {DARK_THEME['card_bg']};
                        }}
                        DropArea:hover {{
                            border-color: {DARK_THEME['accent']};
                        }}
                    """)
                    
                    # Emit the signal with the file path
                    print(f"DropArea: dropEvent - Emitting fileDropped signal with: {filepath}")
                    self.fileDropped.emit(filepath)
                    return  # Process only one CSV file
            
            # If we get here, no CSV files were found
            print("DropArea: dropEvent - No CSV files found among the dropped files")
            event.ignore()
        else:
            print("DropArea: dropEvent - No URLs in mimeData, ignoring")
            event.ignore()

class DataProcessor:
    """Class to handle data processing logic"""
    
    @staticmethod
    def load_csv(filepath):
        """
        Load CSV data from file and return as pandas DataFrame.
        
        Attempts different encodings if the default UTF-8 fails.
        """
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                # Remove CLAN column as per requirements
                if 'CLAN' in df.columns:
                    df = df.drop(columns=['CLAN'])
                return df
            except UnicodeDecodeError:
                # Try the next encoding
                continue
            except Exception as e:
                # For other exceptions, raise immediately
                raise ValueError(f"Error loading CSV file: {str(e)}")
                
        # If we've tried all encodings and none worked
        raise ValueError("Could not decode the CSV file with any supported encoding. Please check the file format.")
    
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
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Enable drop acceptance at the MainWindow level
        self.setAcceptDrops(True)
        
        self.raw_data = None
        self.raw_data_model = None
        self.raw_data_proxy_model = None
        
        self.setup_ui()
        self.setWindowTitle("Total Battle Analyzer")
        self.resize(1200, 800)
        
        # Connect signals and slots
        if hasattr(self, 'drop_area'):
            self.drop_area.fileDropped.connect(self.load_csv_file)
        
        self.statusBar().showMessage("Ready", 3000)
    
    def setup_ui(self):
        """Set up the main UI components"""
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Set up tabs
        self.setup_import_tab()
        self.setup_raw_data_tab()
        self.setup_analysis_tab()
        self.setup_charts_tab()
        
        # Create status bar
        self.statusBar().showMessage("Ready")
    
    def setup_import_tab(self):
        """Setup the import tab UI"""
        import_tab = QWidget()
        layout = QVBoxLayout()
        
        # Add welcome message
        welcome_label = QLabel("Welcome to Total Battle Analyzer")
        welcome_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        welcome_label.setFont(font)
        
        # Add instructions
        instructions = QLabel(
            "Import your CSV file by dragging and dropping it below, or click to select a file."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        
        # Create and add drop area
        self.drop_area = DropArea()
        self.drop_area.fileDropped.connect(self.load_csv_file)
        
        # Create info section
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()
        
        # File info label
        self.file_info_label = QLabel("No file loaded")
        self.file_info_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to info layout
        info_layout.addWidget(self.file_info_label)
        info_group.setLayout(info_layout)
        
        # Add all widgets to main layout
        layout.addStretch()
        layout.addWidget(welcome_label)
        layout.addWidget(instructions)
        layout.addWidget(self.drop_area)
        layout.addWidget(info_group)
        layout.addStretch()
        
        # Set layout for import tab
        import_tab.setLayout(layout)
        
        # Add to tabs
        self.tabs.addTab(import_tab, "Import")
    
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
        
        # Chart data selector
        self.chart_data_selector = QComboBox()
        self.chart_data_selector.addItems(["Player", "Source", "Chest Type"])
        
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
        """Load CSV file and display data"""
        print(f"Loading CSV file: {filepath}")
        self.statusBar().showMessage(f"Loading {filepath}...", 2000)
        
        try:
            # Load CSV data
            self.raw_data = DataProcessor.load_csv(filepath)
            
            if self.raw_data is None or self.raw_data.empty:
                QMessageBox.warning(self, "Warning", "The loaded CSV file contains no data.")
                self.statusBar().showMessage("CSV file loaded but contains no data", 5000)
                return
                
            print(f"Successfully loaded CSV with {len(self.raw_data)} rows and {len(self.raw_data.columns)} columns")
            
            # Update UI with data
            self.update_raw_data_view()
            self.analyze_data()
            
            # Switch to Raw Data tab
            self.tabs.setCurrentIndex(1)
            
            self.statusBar().showMessage(f"Loaded {len(self.raw_data)} records from {filepath}", 5000)
            
            # Store the file path
            self.current_filepath = filepath
            
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
            self.statusBar().showMessage("Unexpected error loading CSV file", 5000)
            print(f"Unexpected error: {str(e)}")
            
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
        """Update the chart based on the selected chart type and data"""
        if not hasattr(self, 'analysis_results') or self.analysis_results is None:
            return
            
        chart_type = self.chart_type_selector.currentText()
        data_type = self.chart_data_selector.currentText()
        
        # Clear previous chart
        self.mpl_canvas.fig.clear()
        self.mpl_canvas.axes = self.mpl_canvas.fig.add_subplot(111)
        
        # Determine which data to use
        if data_type == "Player":
            df = self.analysis_results['player_totals'].head(10)
            x_label = 'Player'
            data_column = 'PLAYER'
        elif data_type == "Source":
            df = self.analysis_results['source_totals'].head(10)
            x_label = 'Source'
            data_column = 'SOURCE'
        elif data_type == "Chest Type":
            df = self.analysis_results['chest_totals'].head(10)
            x_label = 'Chest Type'
            data_column = 'CHEST'
        else:
            return
            
        # Create chart based on type
        if chart_type == "Bar Chart":
            self.mpl_canvas.axes.barh(df[data_column], df['SCORE'], color=DARK_THEME['accent'])
            self.mpl_canvas.axes.set_title(f'Top 10 {data_type}s by Score', color=DARK_THEME['foreground'])
            self.mpl_canvas.axes.set_xlabel('Score', color=DARK_THEME['foreground'])
            self.mpl_canvas.axes.set_ylabel(x_label, color=DARK_THEME['foreground'])
            
        elif chart_type == "Pie Chart":
            wedges, texts, autotexts = self.mpl_canvas.axes.pie(
                df['SCORE'], 
                labels=df[data_column], 
                autopct='%1.1f%%',
                colors=[QColor(DARK_THEME['accent']).lighter(100 + i*20).name() for i in range(len(df))]
            )
            self.mpl_canvas.axes.set_title(f'Score Distribution by {data_type}', color=DARK_THEME['foreground'])
            # Make text visible on dark background
            for text in texts:
                text.set_color(DARK_THEME['foreground'])
            for autotext in autotexts:
                autotext.set_color('white')
                
        elif chart_type == "Line Chart":
            if data_type == "Player":
                # For line chart with player data, create a time series
                player_dates = self.raw_data.groupby(['DATE', 'PLAYER'])['SCORE'].sum().reset_index()
                top_players = df[data_column].tolist()
                for player in top_players[:5]:  # Limit to 5 players for clarity
                    player_data = player_dates[player_dates['PLAYER'] == player]
                    self.mpl_canvas.axes.plot(player_data['DATE'], player_data['SCORE'], marker='o', label=player)
                self.mpl_canvas.axes.set_title(f'Score Timeline by Player', color=DARK_THEME['foreground'])
                self.mpl_canvas.axes.set_xlabel('Date', color=DARK_THEME['foreground'])
                self.mpl_canvas.axes.set_ylabel('Score', color=DARK_THEME['foreground'])
                self.mpl_canvas.axes.legend()
            else:
                # For other data types, use a simple trend line
                df = df.sort_values('SCORE')
                self.mpl_canvas.axes.plot(df[data_column], df['SCORE'], marker='o', color=DARK_THEME['accent'])
                self.mpl_canvas.axes.set_title(f'Score Trend by {data_type}', color=DARK_THEME['foreground'])
                self.mpl_canvas.axes.set_xlabel(x_label, color=DARK_THEME['foreground'])
                self.mpl_canvas.axes.set_ylabel('Score', color=DARK_THEME['foreground'])
            
            self.mpl_canvas.axes.tick_params(axis='x', rotation=45)
        
        # Update the canvas
        self.mpl_canvas.fig.tight_layout()
        self.mpl_canvas.draw()
    
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
        
        # Ask for save location
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis", default_filename, "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                df.to_csv(filepath, index=False)
                self.statusBar().showMessage(f"Exported to {filepath}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
                self.statusBar().showMessage("Error exporting data", 5000)

    # Forward drag events to the drop area if it exists
    def dragEnterEvent(self, event):
        print(f"MainWindow: dragEnterEvent - mimeData formats: {event.mimeData().formats()}")
        
        # Only handle drag events when on the Import tab
        if self.tabs.currentIndex() == 0:
            if event.mimeData().hasUrls():
                # Check if any of the URLs are CSV files
                has_csv = False
                for url in event.mimeData().urls():
                    filepath = url.toLocalFile()
                    print(f"MainWindow: dragEnterEvent - Checking file: {filepath}")
                    if filepath.lower().endswith('.csv'):
                        has_csv = True
                        break
                        
                if has_csv:
                    print("MainWindow: dragEnterEvent - Found CSV file, accepting")
                    event.acceptProposedAction()
                else:
                    print("MainWindow: dragEnterEvent - No CSV files, ignoring")
                    event.ignore()
            else:
                print("MainWindow: dragEnterEvent - No URLs in mimeData, ignoring")
                event.ignore()
        else:
            print("MainWindow: dragEnterEvent - Not on Import tab, ignoring")
            event.ignore()
            
    def dragMoveEvent(self, event):
        print("MainWindow: dragMoveEvent")
        
        # Only handle drag events when on the Import tab
        if self.tabs.currentIndex() == 0:
            if event.mimeData().hasUrls():
                # Check if any of the URLs are CSV files
                has_csv = False
                for url in event.mimeData().urls():
                    filepath = url.toLocalFile()
                    if filepath.lower().endswith('.csv'):
                        has_csv = True
                        break
                        
                if has_csv:
                    event.acceptProposedAction()
                else:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        print(f"MainWindow: dropEvent - mimeData formats: {event.mimeData().formats()}")
        
        # Only handle drop events when on the Import tab
        if self.tabs.currentIndex() == 0:
            if event.mimeData().hasUrls():
                # Process all URLs and find the first CSV file
                for url in event.mimeData().urls():
                    filepath = url.toLocalFile()
                    print(f"MainWindow: dropEvent - Processing file: {filepath}")
                    
                    if filepath.lower().endswith('.csv'):
                        print(f"MainWindow: dropEvent - Found CSV file: {filepath}")
                        # Accept the drop operation
                        event.acceptProposedAction()
                        
                        # Load the CSV file
                        print(f"MainWindow: dropEvent - Loading CSV file: {filepath}")
                        self.load_csv_file(filepath)
                        return  # Process only the first CSV file
                
                # If we reach here, no CSV files were found
                print("MainWindow: dropEvent - No CSV files found, ignoring")
                event.ignore()
            else:
                print("MainWindow: dropEvent - No URLs in mimeData, ignoring")
                event.ignore()
        else:
            print("MainWindow: dropEvent - Not on Import tab, ignoring")
            event.ignore()

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    # Apply dark theme
    StyleManager.apply_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

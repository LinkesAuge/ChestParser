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
    QColor, QPalette, QFont, QIcon, QPixmap, QPainter
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
        
        # Debug flag for verbose logging
        self.debug = True
        
        layout = QVBoxLayout()
        
        self.label = QLabel("Drop CSV file here")
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        
        self.description = QLabel("or use buttons below")
        self.description.setAlignment(Qt.AlignCenter)
        
        # Add explicit import button
        self.import_button = QPushButton("Select CSV File")
        self.import_button.clicked.connect(self.open_file_dialog)
        self.import_button.setMinimumHeight(40)
        self.import_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {DARK_THEME['accent']};
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {DARK_THEME['accent_hover']};
            }}
        """)
        
        # Create a QLabel with an icon for import
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Create a pixmap with a document icon (using Unicode character)
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_pixmap = QPixmap(64, 64)
        icon_pixmap.fill(Qt.transparent)
        painter = QPainter(icon_pixmap)
        painter.setFont(icon_font)
        painter.setPen(QColor(DARK_THEME['accent']))
        painter.drawText(icon_pixmap.rect(), Qt.AlignCenter, "📄")
        painter.end()
        
        self.icon_label.setPixmap(icon_pixmap)
        self.icon_label.setMinimumHeight(80)
        
        layout.addStretch()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.label)
        layout.addWidget(self.description)
        layout.addSpacing(20)
        layout.addWidget(self.import_button)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMinimumHeight(200)
        
        # Style the drop area
        self._update_style(False)
    
    def open_file_dialog(self):
        """Open a file dialog to select a CSV file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if filepath:
            self.fileDropped.emit(filepath)
            
    def _update_style(self, highlight=False):
        """Update the style of the drop area with optional highlighting"""
        if highlight:
            self.setStyleSheet(f"""
                DropArea {{
                    border: 2px dashed {DARK_THEME['accent']};
                    border-radius: 8px;
                    background-color: {DARK_THEME['card_bg']};
                }}
            """)
        else:
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
        self.open_file_dialog()
        
    # Keep our existing drag and drop implementation
    def dragEnterEvent(self, event):
        if self.debug:
            self.print_mime_data(event, "dragEnterEvent")
        
        try:
            # Accept ANY drag initially - crucial for Windows to show drop is possible
            has_urls = event.mimeData().hasUrls()
            if has_urls:
                event.acceptProposedAction()
                self._update_style(True)
                return
                
        except Exception as e:
            print(f"ERROR in dragEnterEvent: {str(e)}")
        
        event.ignore()
        
    def dragMoveEvent(self, event):
        if self.debug:
            print("DropArea: dragMoveEvent")
        
        try:
            # Continue accepting the drag
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                return
        except Exception as e:
            print(f"ERROR in dragMoveEvent: {str(e)}")
        
        event.ignore()
        
    def dragLeaveEvent(self, event):
        if self.debug:
            print("DropArea: dragLeaveEvent")
        
        # Reset style
        self._update_style(False)
        event.accept()
    
    def dropEvent(self, event):
        if self.debug:
            self.print_mime_data(event, "dropEvent")
        
        # Reset style first thing
        self._update_style(False)
        
        # Process dropped files
        try:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                
                # Process each URL (file)
                for url in urls:
                    try:
                        # Convert URL to local file path (different methods for robustness)
                        filepath = url.toLocalFile()
                        if not filepath and url.isLocalFile():
                            filepath = url.path()
                            # Remove leading slash on Windows if it exists
                            if filepath.startswith('/') and ':' in filepath:
                                filepath = filepath[1:]
                        
                        # Now check file type
                        if filepath.lower().endswith('.csv'):
                            # Accept the event
                            event.setDropAction(Qt.CopyAction)
                            event.acceptProposedAction()
                            
                            # Emit signal with file path
                            self.fileDropped.emit(filepath)
                            return True
                    except Exception as e:
                        print(f"ERROR processing URL {url.toString()}: {str(e)}")
        except Exception as e:
            print(f"ERROR in dropEvent: {str(e)}")
        
        event.ignore()
        return False
        
    def print_mime_data(self, event, event_name):
        """Debug helper to print detailed information about MIME data in an event"""
        try:
            print(f"\n=== {event_name} MIME Data Debug ===")
            print(f"Event type: {event.type()}")
            print(f"Drop action: {event.dropAction()}")
            print(f"Proposed action: {event.proposedAction()}")
            print(f"Possible actions: {event.possibleActions()}")
            
            mime_data = event.mimeData()
            print(f"Has URLs: {mime_data.hasUrls()}")
            print(f"MIME formats: {mime_data.formats()}")
            
            if mime_data.hasUrls():
                urls = mime_data.urls()
                print(f"URL count: {len(urls)}")
                for i, url in enumerate(urls):
                    print(f"  URL {i}: {url.toString()}")
                    print(f"    isLocalFile: {url.isLocalFile()}")
                    print(f"    toLocalFile: {url.toLocalFile()}")
                    print(f"    path: {url.path()}")
                    print(f"    scheme: {url.scheme()}")
                    
            print("=== End MIME Data Debug ===\n")
        except Exception as e:
            print(f"Error in print_mime_data: {str(e)}")
            
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
                first_bytes = f.read(16)
                if DataProcessor.debug:
                    print(f"First bytes: {first_bytes}")
        except Exception as e:
            error_msg = f"Failed to open file: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
        
        # List of encodings to try, in order of preference
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
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
                
                # Remove CLAN column as per requirements
                if 'CLAN' in df.columns:
                    df = df.drop(columns=['CLAN'])
                    if DataProcessor.debug:
                        print("Removed CLAN column")
                
                # Check if required columns are present
                required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    warning_msg = f"Warning: Missing required columns: {missing_columns}"
                    print(warning_msg)
                    # Continue anyway - user might want to view the data regardless
                
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
                raise ValueError(error_msg)
                
            except Exception as e:
                # For other exceptions, log and raise immediately
                error_msg = f"Error loading CSV file with {encoding}: {str(e)}"
                print(error_msg)
                raise ValueError(error_msg)
                
        # If we've tried all encodings and none worked
        error_msg = "Could not decode the CSV file with any supported encoding. Please check the file format."
        if last_error:
            error_msg += f" Last error: {str(last_error)}"
            
        print(error_msg)
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
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Enable drop acceptance at the MainWindow level
        self.setAcceptDrops(True)
        
        # Debug flag for verbose logging
        self.debug = True
        
        self.raw_data = None
        self.raw_data_model = None
        self.raw_data_proxy_model = None
        self.current_filepath = None
        
        self.setup_ui()
        self.setup_menu()
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
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv)"
        )
        if filepath:
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
        
        # Add welcome message
        welcome_label = QLabel("Welcome to Total Battle Analyzer")
        welcome_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        welcome_label.setFont(font)
        
        # Add instructions
        instructions = QLabel(
            "Import your CSV file by dragging and dropping it below, clicking the area, or using the Import button in the File menu."
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
        try:
            # Normalize filepath for Windows
            filepath = Path(filepath).resolve().as_posix()
            
            if self.debug:
                print(f"Loading CSV file: {filepath}")
                print(f"File exists: {os.path.exists(filepath)}")
                print(f"File readable: {os.access(filepath, os.R_OK)}")
                print(f"File size: {os.path.getsize(filepath) if os.path.exists(filepath) else 'N/A'}")
            
            self.statusBar().showMessage(f"Loading {filepath}...", 2000)
            
            try:
                # Load CSV data with improved error handling
                self.raw_data = DataProcessor.load_csv(filepath)
                
                if self.raw_data is None or self.raw_data.empty:
                    QMessageBox.warning(self, "Warning", "The loaded CSV file contains no data.")
                    self.statusBar().showMessage("CSV file loaded but contains no data", 5000)
                    return
                    
                print(f"Successfully loaded CSV with {len(self.raw_data)} rows and {len(self.raw_data.columns)} columns")
                print(f"Columns: {self.raw_data.columns.tolist()}")
                print(f"First row: {self.raw_data.iloc[0].tolist() if not self.raw_data.empty else 'N/A'}")
                
                # Update UI with data
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
                print(f"Unexpected error in load_csv: {str(e)}")
                
        except Exception as e:
            # Catch errors in the outer block too
            error_msg = f"Error processing filepath: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.statusBar().showMessage("Error processing file path", 5000)
            print(f"Error in load_csv_file outer block: {str(e)}")
    
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

    def dragEnterEvent(self, event):
        """Handle drag enter events at the MainWindow level"""
        if self.debug:
            print("MainWindow: dragEnterEvent")
        
        # Only accept when on the Import tab
        if self.tabs.currentIndex() == 0 and event.mimeData().hasUrls():
            # Accept the event to show the user that dropping is possible
            event.acceptProposedAction()
            # Update the drop area style if available
            if hasattr(self, 'drop_area'):
                self.drop_area._update_style(True)
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """Handle drag move events at the MainWindow level"""
        if self.debug:
            print("MainWindow: dragMoveEvent")
        
        # Only accept when on the Import tab
        if self.tabs.currentIndex() == 0 and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle drop events at the MainWindow level"""
        if self.debug:
            print("MainWindow: dropEvent")
            if hasattr(self, 'drop_area'):
                self.drop_area.print_mime_data(event, "MainWindow dropEvent")
        
        # Reset drop area style if available
        if hasattr(self, 'drop_area'):
            self.drop_area._update_style(False)
        
        # Process the drop event when on the Import tab
        if self.tabs.currentIndex() == 0 and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            
            # Try different methods to get a valid file path
            for url in urls:
                try:
                    # Method 1: Use toLocalFile
                    filepath = url.toLocalFile()
                    
                    # Method 2: If that failed, try path()
                    if not filepath and url.isLocalFile():
                        filepath = url.path()
                        # Remove leading slash on Windows if it exists
                        if filepath.startswith('/') and ':' in filepath:
                            filepath = filepath[1:]
                    
                    # Method 3: As a last resort, try to create a Path object
                    if not filepath:
                        # Try to get a string representation and convert it
                        filepath = str(url.toString())
                        if filepath.startswith('file:///'):
                            filepath = filepath[8:]  # Remove file:///
                    
                    if self.debug:
                        print(f"Extracted file path: {filepath}")
                        print(f"File exists check: {os.path.exists(filepath)}")
                    
                    # Check if it's a CSV file
                    if filepath.lower().endswith('.csv'):
                        event.acceptProposedAction()
                        self.load_csv_file(filepath)
                        return True
                except Exception as e:
                    print(f"Error processing URL {url.toString()}: {str(e)}")
        
        event.ignore()
        return False

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

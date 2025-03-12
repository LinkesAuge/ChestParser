# importarea.py - ImportArea class implementation
from modules.utils import *
from modules.stylemanager import DARK_THEME
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QGroupBox)
from PySide6.QtCore import Signal, Qt
from pathlib import Path

class ImportArea(QWidget):
    """
    Widget for importing CSV files via file selection.
    Provides a styled interface for users to select CSV files and displays import instructions.
    """
    
    fileSelected = Signal(str)
    
    def __init__(self, parent=None, debug=False):
        """
        Initialize the ImportArea widget.
        
        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
            debug (bool, optional): Enable debug output. Defaults to False.
        """
        super().__init__(parent)
        self.debug = debug
        self.main_window = self.get_main_window()
        self._setup_ui()
    
    def get_main_window(self):
        """Find the main window parent"""
        parent = self.parent()
        while parent is not None:
            if parent.__class__.__name__ == 'MainWindow':
                return parent
            parent = parent.parent()
        return None
    
    def _setup_ui(self):
        """Set up the UI components with proper styling and layout"""
        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create instructions group box
        instructions_group = QGroupBox("Import Instructions")
        instructions_group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {DARK_THEME['accent']};
                border-radius: 5px;
                margin-top: 1em;
                padding: 10px;
                color: {DARK_THEME['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: {DARK_THEME['accent']};
            }}
        """)
        
        instructions_layout = QVBoxLayout()
        instructions_text = QLabel(
            "CSV files must contain these columns:\n"
            "- DATE (format: YYYY-MM-DD)\n"
            "- PLAYER (player name)\n"
            "- SOURCE (chest source)\n"
            "- CHEST (chest type)\n"
            "- SCORE (numeric value)\n\n"
            "Files missing any required columns will be rejected.\n"
            "Additional columns will be removed."
        )
        instructions_text.setStyleSheet(f"color: {DARK_THEME['text']};")
        instructions_text.setWordWrap(True)
        instructions_layout.addWidget(instructions_text)
        instructions_group.setLayout(instructions_layout)
        
        # Create file selection button with styling
        self.select_button = QPushButton("Select CSV File")
        self.select_button.setMinimumHeight(40)
        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_THEME['button_gradient_start']},
                    stop:1 {DARK_THEME['button_gradient_end']});
                border: 1px solid {DARK_THEME['accent']};
                border-radius: 5px;
                color: {DARK_THEME['text']};
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DARK_THEME['button_hover_gradient_start']},
                    stop:1 {DARK_THEME['button_hover_gradient_end']});
            }}
            QPushButton:pressed {{
                background: {DARK_THEME['button_pressed']};
            }}
        """)
        self.select_button.clicked.connect(self.open_file_dialog)
        
        # Create file info label with styling
        self.file_info = QLabel("No file selected")
        self.file_info.setAlignment(Qt.AlignCenter)
        self.file_info.setStyleSheet(f"""
            QLabel {{
                color: {DARK_THEME['text']};
                padding: 5px;
                background: {DARK_THEME['background_secondary']};
                border: 1px solid {DARK_THEME['accent']};
                border-radius: 3px;
            }}
        """)
        
        # Add widgets to layout
        layout.addWidget(instructions_group)
        layout.addWidget(self.select_button)
        layout.addWidget(self.file_info)
        
        # Set widget styling
        self.setStyleSheet(f"""
            QWidget {{
                background: {DARK_THEME['background']};
            }}
        """)
        
        # Set layout
        self.setLayout(layout)
    
    def open_file_dialog(self):
        """Open a file dialog to select a CSV file"""
        start_dir = ""
        if self.main_window and hasattr(self.main_window, 'config_manager'):
            # Get the import directory from config
            start_dir = self.main_window.config_manager.get_import_directory()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", start_dir, "CSV Files (*.csv)"
        )
        
        if filepath:
            if self.debug:
                print(f"File selected via dialog: {filepath}")
            
            # Update file info label
            self.file_info.setText(f"Selected: {os.path.basename(filepath)}")
            
            # Update import directory in config if possible
            if self.main_window and hasattr(self.main_window, 'config_manager'):
                self.main_window.config_manager.set_import_directory(str(Path(filepath).parent))
            
            # Emit signal with filepath
            self.fileSelected.emit(filepath)



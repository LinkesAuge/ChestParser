# droparea.py - DropArea class implementation
from modules.utils import *
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent
from pathlib import Path
from .stylemanager import DARK_THEME
import os

class DropArea(QWidget):
    """
    A widget that accepts file drops and displays instructions for file selection.
    Provides both drag-and-drop and click-to-select functionality.
    """
    
    fileDropped = Signal(str)
    
    def __init__(self, parent=None, debug=False):
        """
        Initialize the DropArea widget.
        
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
        """Set up the UI components with proper styling"""
        # Enable drop events
        self.setAcceptDrops(True)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Create title label
        self.title_label = QLabel("Drop CSV File Here")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {DARK_THEME['text']};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        
        # Create instruction label
        self.instruction_label = QLabel("or click to select file")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(f"""
            QLabel {{
                color: {DARK_THEME['text_disabled']};
                font-size: 12px;
            }}
        """)
        
        # Try to load and set the icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'drop_icon.png')
            if os.path.exists(icon_path):
                self.icon_label = QLabel()
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(scaled_pixmap)
                self.icon_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.icon_label)
        except Exception as e:
            if self.debug:
                print(f"Failed to load drop icon: {e}")
        
        # Add labels to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.instruction_label)
        
        # Set layout
        self.setLayout(layout)
        
        # Set widget styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_THEME['background_secondary']};
                border: 2px dashed {DARK_THEME['accent']};
                border-radius: 10px;
            }}
        """)
        
        # Set minimum size
        self.setMinimumSize(200, 200)
    
    def mousePressEvent(self, event):
        """Handle mouse press events to open file dialog"""
        self.open_file_dialog()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {DARK_THEME['background_secondary']};
                    border: 2px dashed {DARK_THEME['accent_hover']};
                    border-radius: 10px;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_THEME['background_secondary']};
                border: 2px dashed {DARK_THEME['accent']};
                border-radius: 10px;
            }}
        """)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath.lower().endswith('.csv'):
                if self.debug:
                    print(f"File dropped: {filepath}")
                self.fileDropped.emit(filepath)
        
        # Reset styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_THEME['background_secondary']};
                border: 2px dashed {DARK_THEME['accent']};
                border-radius: 10px;
            }}
        """)
    
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
            
            # Update import directory in config if possible
            if self.main_window and hasattr(self.main_window, 'config_manager'):
                self.main_window.config_manager.set_import_directory(str(Path(filepath).parent))
            
            # Emit signal with filepath
            self.fileDropped.emit(filepath)



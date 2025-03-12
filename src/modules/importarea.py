# importarea.py - ImportArea class implementation
from modules.utils import *
from modules.stylemanager import DARK_THEME
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QGroupBox, QHBoxLayout, QFrame,
                             QSplitter)
from PySide6.QtCore import Signal, Qt
from pathlib import Path
import os  # For os.path.basename

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
        self.config_manager = None
        self._setup_ui()
    
    def set_config_manager(self, config_manager):
        """
        Set the configuration manager for this import area.
        
        Args:
            config_manager: The configuration manager instance to use
        """
        self.config_manager = config_manager
        if self.debug:
            print("ConfigManager set for ImportArea")
    
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Create a welcome header
        welcome_layout = QVBoxLayout()
        welcome_title = QLabel("Total Battle Analyzer")
        welcome_title.setStyleSheet(f"""
            color: {DARK_THEME['accent']};
            font-size: 24px;
            font-weight: bold;
        """)
        welcome_title.setAlignment(Qt.AlignCenter)
        
        welcome_subtitle = QLabel("Import your data to begin analysis")
        welcome_subtitle.setStyleSheet(f"""
            color: {DARK_THEME['text_secondary']};
            font-size: 16px;
        """)
        welcome_subtitle.setAlignment(Qt.AlignCenter)
        
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)
        welcome_layout.addSpacing(10)
        
        layout.addLayout(welcome_layout)
        
        # Create horizontal splitter for layout
        content_splitter = QSplitter(Qt.Horizontal)
        
        # File selection panel (left side)
        file_panel = QWidget()
        file_panel.setObjectName("fileInputSection")
        file_layout = QVBoxLayout(file_panel)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(15)
        
        # File selection icon/instructions
        file_header = QLabel("Select CSV File")
        file_header.setStyleSheet(f"""
            color: {DARK_THEME['accent']};
            font-size: 18px;
            font-weight: bold;
        """)
        file_header.setAlignment(Qt.AlignCenter)
        
        file_instruction = QLabel("Click the button below to select your CSV data file")
        file_instruction.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        file_instruction.setAlignment(Qt.AlignCenter)
        file_instruction.setWordWrap(True)
        
        # Create file selection button with enhanced styling
        self.select_button = QPushButton("Select CSV File")
        self.select_button.setObjectName("selectFileButton")
        self.select_button.setMinimumHeight(40)
        self.select_button.clicked.connect(self.open_file_dialog)
        
        # Create file info label with styling
        self.file_info = QLabel("No file selected")
        self.file_info.setAlignment(Qt.AlignCenter)
        self.file_info.setStyleSheet(f"""
            color: {DARK_THEME['text']};
            padding: 10px;
            background: {DARK_THEME['background_light']};
            border: 1px solid {DARK_THEME['border']};
            border-radius: 5px;
            font-size: 13px;
        """)
        
        # Add widgets to file panel
        file_layout.addWidget(file_header)
        file_layout.addWidget(file_instruction)
        file_layout.addSpacing(20)
        file_layout.addWidget(self.select_button)
        file_layout.addWidget(self.file_info)
        file_layout.addStretch()
        
        # Instructions panel (right side)
        instructions_panel = QWidget()
        instructions_layout = QVBoxLayout(instructions_panel)
        instructions_layout.setContentsMargins(10, 10, 10, 10)
        instructions_layout.setSpacing(10)
        
        # Create instructions group box
        instructions_group = QGroupBox("File Requirements")
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
                font-weight: bold;
            }}
        """)
        
        instructions_box_layout = QVBoxLayout()
        instructions_text = QLabel(
            "CSV files must contain these columns:\n\n"
            "• DATE (format: YYYY-MM-DD)\n"
            "• PLAYER (player name)\n"
            "• SOURCE (chest source)\n"
            "• CHEST (chest type)\n"
            "• SCORE (numeric value)\n\n"
            "Files missing any required columns will be rejected.\n"
            "Additional columns like CLAN will be preserved."
        )
        instructions_text.setStyleSheet(f"color: {DARK_THEME['text']}; line-height: 150%;")
        instructions_text.setWordWrap(True)
        instructions_box_layout.addWidget(instructions_text)
        instructions_group.setLayout(instructions_box_layout)
        
        # Note box
        note_frame = QFrame()
        note_frame.setStyleSheet(f"""
            background-color: {DARK_THEME['background_light']};
            border-radius: 5px;
            padding: 5px;
        """)
        note_layout = QVBoxLayout(note_frame)
        
        note_label = QLabel("Note:")
        note_label.setStyleSheet(f"color: {DARK_THEME['accent']}; font-weight: bold;")
        
        note_text = QLabel(
            "This application can auto-detect column names (case-insensitive) "
            "and supports multiple encodings including UTF-8 and Windows formats. "
            "German umlauts (ä, ö, ü) are properly supported."
        )
        note_text.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
        note_text.setWordWrap(True)
        
        note_layout.addWidget(note_label)
        note_layout.addWidget(note_text)
        
        # Add widgets to instructions panel
        instructions_layout.addWidget(instructions_group)
        instructions_layout.addWidget(note_frame)
        instructions_layout.addStretch()
        
        # Add panels to splitter
        content_splitter.addWidget(file_panel)
        content_splitter.addWidget(instructions_panel)
        
        # Set splitter sizes (40% file panel, 60% instructions)
        content_splitter.setSizes([4, 6])
        
        # Add splitter to main layout
        layout.addWidget(content_splitter)
        
        # Set layout
        self.setLayout(layout)
    
    def open_file_dialog(self):
        """Open a file dialog to select a CSV file"""
        if self.debug:
            print(f"\n--- IMPORTAREA.OPEN_FILE_DIALOG CALLED ---\n")
            import traceback
            traceback.print_stack()  # Print stack trace to identify caller
        
        # Use a static/class-level flag to ensure only one dialog is active across all instances
        if hasattr(ImportArea, '_dialog_active') and ImportArea._dialog_active:
            if self.debug:
                print("A file dialog is already active, ignoring duplicate call")
            return
        
        # Set dialog active at class level
        ImportArea._dialog_active = True
        
        # Also set the dialog active flag in the main window if it exists
        # This is for compatibility with existing code that checks this flag
        if self.main_window and hasattr(self.main_window, '_file_dialog_active'):
            self.main_window._file_dialog_active = True
        
        try:
            start_dir = ""
            # First try to use the local config_manager if available
            if self.config_manager is not None:
                start_dir = self.config_manager.get_import_directory()
                if self.debug:
                    print(f"Using import directory from local config_manager: {start_dir}")
            # Fall back to main_window's config_manager if needed
            elif self.main_window and hasattr(self.main_window, 'config_manager'):
                start_dir = self.main_window.config_manager.get_import_directory()
                if self.debug:
                    print(f"Using import directory from main_window.config_manager: {start_dir}")
            
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Open CSV File", start_dir, "CSV Files (*.csv)"
            )
            
            if filepath:
                if self.debug:
                    print(f"File selected via dialog: {filepath}")
                
                # Update file info label
                self.file_info.setText(f"Selected: {os.path.basename(filepath)}")
                
                # Update import directory in config if possible
                # First try to use the local config_manager if available
                if self.config_manager is not None:
                    self.config_manager.set_import_directory(str(Path(filepath).parent))
                    if self.debug:
                        print(f"Updated import directory in local config_manager: {str(Path(filepath).parent)}")
                # Fall back to main_window's config_manager if needed
                elif self.main_window and hasattr(self.main_window, 'config_manager'):
                    self.main_window.config_manager.set_import_directory(str(Path(filepath).parent))
                    if self.debug:
                        print(f"Updated import directory in main_window.config_manager: {str(Path(filepath).parent)}")
                
                # Emit signal with filepath
                if self.debug:
                    print(f"Emitting fileSelected signal with: {filepath}")
                self.fileSelected.emit(filepath)
        finally:
            # Reset the dialog active flags
            if hasattr(ImportArea, '_dialog_active'):
                ImportArea._dialog_active = False
            
            # Also reset the main window flag for compatibility
            if self.main_window and hasattr(self.main_window, '_file_dialog_active'):
                self.main_window._file_dialog_active = False



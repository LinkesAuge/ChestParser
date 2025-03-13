# Total Battle Analyzer Refactoring Plan: Phase 4 - Part 3
## Application Screens

This document details the implementation of application-specific screens for the Total Battle Analyzer application as part of Phase 4 refactoring.

### Introduction

After implementing the UI foundation (Part 1) and creating reusable UI components (Part 2), we now need to implement application-specific screens that will form the main interface for users. These screens will utilize the components developed in Part 2 and follow the architecture established in Part 1.

Application screens represent the various functionalities of the Total Battle Analyzer, including:
- Data Import Screen
- Raw Data Viewing Screen
- Analysis Screen
- Charts and Visualization Screen
- Report Generation Screen

Each screen will be implemented as a distinct module that integrates with the main application window and utilizes appropriate UI components for its specific functionality.

### 1. Setup and Preparation

- [ ] **Create Screen Base Framework**
  - [ ] Create the `src/ui/screens` directory to house all application screens
  - [ ] Create `src/ui/screens/__init__.py` to make it a proper package
  - [ ] Create a base screen class in `src/ui/screens/base_screen.py`:
    ```python
    # src/ui/screens/base_screen.py
    from typing import Optional, Dict, Any, List
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
    from PySide6.QtCore import Qt, Signal

    class BaseScreen(QWidget):
        """Base class for all application screens."""
        
        # Signals
        data_changed = Signal()
        screen_action = Signal(str, object)
        
        def __init__(self, parent=None):
            """
            Initialize the base screen.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Create main layout
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(10, 10, 10, 10)
            self.layout.setSpacing(10)
            self.setLayout(self.layout)
            
            # Initialize properties
            self._data = {}
            self._config = {}
            
            # Set up the screen
            self._setup_ui()
            
        def _setup_ui(self):
            """Set up the user interface."""
            # To be implemented by subclasses
            pass
            
        def load_data(self, data: Dict[str, Any]) -> None:
            """
            Load data into the screen.
            
            Args:
                data: Dictionary containing the data to load
            """
            self._data = data.copy() if data else {}
            self._update_ui()
            
        def _update_ui(self) -> None:
            """Update the UI with the current data."""
            # To be implemented by subclasses
            pass
            
        def set_config(self, config: Dict[str, Any]) -> None:
            """
            Set configuration options for the screen.
            
            Args:
                config: Dictionary containing configuration options
            """
            self._config = config.copy() if config else {}
            self._apply_config()
            
        def _apply_config(self) -> None:
            """Apply the current configuration to the screen."""
            # To be implemented by subclasses
            pass
            
        def get_data(self) -> Dict[str, Any]:
            """
            Get the current data from the screen.
            
            Returns:
                Dictionary containing the current data
            """
            return self._data.copy()
            
        def clear(self) -> None:
            """Clear the screen and reset its state."""
            self._data = {}
            self._update_ui()
    ```

- [ ] **Create Screen Manager**
  - [ ] Create `src/ui/screens/screen_manager.py` to manage screen navigation:
    ```python
    # src/ui/screens/screen_manager.py
    from typing import Dict, Optional, Type, List
    from PySide6.QtWidgets import QStackedWidget, QWidget
    from .base_screen import BaseScreen
    
    class ScreenManager(QStackedWidget):
        """Manager for application screens."""
        
        def __init__(self, parent=None):
            """
            Initialize the screen manager.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Store registered screens
            self.screens: Dict[str, BaseScreen] = {}
            
        def register_screen(self, screen_id: str, screen: BaseScreen) -> None:
            """
            Register a screen with the manager.
            
            Args:
                screen_id: Unique identifier for the screen
                screen: The screen widget to register
            """
            if screen_id in self.screens:
                # Replace existing screen
                old_index = self.indexOf(self.screens[screen_id])
                if old_index >= 0:
                    self.removeWidget(self.screens[screen_id])
            
            # Add the new screen
            self.screens[screen_id] = screen
            self.addWidget(screen)
            
            # Connect signals
            screen.screen_action.connect(lambda action, data: self._handle_screen_action(screen_id, action, data))
            
        def show_screen(self, screen_id: str) -> bool:
            """
            Show a registered screen.
            
            Args:
                screen_id: Identifier of the screen to show
                
            Returns:
                True if the screen was found and shown, False otherwise
            """
            if screen_id in self.screens:
                self.setCurrentWidget(self.screens[screen_id])
                return True
            return False
            
        def get_screen(self, screen_id: str) -> Optional[BaseScreen]:
            """
            Get a registered screen by ID.
            
            Args:
                screen_id: Identifier of the screen to retrieve
                
            Returns:
                The requested screen or None if not found
            """
            return self.screens.get(screen_id)
            
        def get_current_screen_id(self) -> Optional[str]:
            """
            Get the ID of the currently visible screen.
            
            Returns:
                The ID of the current screen or None if no screen is visible
            """
            current_widget = self.currentWidget()
            for screen_id, screen in self.screens.items():
                if screen == current_widget:
                    return screen_id
            return None
            
        def _handle_screen_action(self, source_id: str, action: str, data: object) -> None:
            """
            Handle actions from screens.
            
            Args:
                source_id: ID of the screen that triggered the action
                action: Action identifier string
                data: Additional data for the action
            """
            # Common screen navigation
            if action == "navigate":
                if isinstance(data, str):
                    self.show_screen(data)
            
            # Forward any other actions to the parent widget
            if hasattr(self, "screen_action"):
                self.screen_action.emit(source_id, action, data)
    ```

- [ ] **Set Up Screen Factory**
  - [ ] Create `src/ui/screens/screen_factory.py` to create screen instances:
    ```python
    # src/ui/screens/screen_factory.py
    from typing import Dict, Any, Optional, Type
    from .base_screen import BaseScreen
    from .import_screen import ImportScreen
    from .raw_data_screen import RawDataScreen
    from .analysis_screen import AnalysisScreen
    from .charts_screen import ChartsScreen
    from .report_screen import ReportScreen
    
    class ScreenFactory:
        """Factory for creating application screens."""
        
        # Screen type mapping
        SCREEN_TYPES = {
            'import': ImportScreen,
            'raw_data': RawDataScreen,
            'analysis': AnalysisScreen,
            'charts': ChartsScreen,
            'report': ReportScreen
        }
        
        @classmethod
        def create_screen(cls, screen_type: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseScreen]:
            """
            Create a screen instance of the specified type.
            
            Args:
                screen_type: Type of screen to create
                config: Optional configuration for the screen
                
            Returns:
                The created screen or None if the type is not supported
            """
            if screen_type not in cls.SCREEN_TYPES:
                return None
                
            # Create the screen
            screen_class = cls.SCREEN_TYPES[screen_type]
            screen = screen_class()
            
            # Apply configuration if provided
            if config:
                screen.set_config(config)
                
            return screen
            
        @classmethod
        def get_available_screen_types(cls) -> list:
            """
            Get a list of available screen types.
            
            Returns:
                List of supported screen type identifiers
            """
            return list(cls.SCREEN_TYPES.keys())
    ```

- [ ] **Set Up Main Window Integration**
  - [ ] Update `src/ui/main_window.py` to use the screen manager:
    ```python
    # In the MainWindow.__init__ method
    
    # Create screen manager
    self.screen_manager = ScreenManager()
    self.central_layout.addWidget(self.screen_manager, 1)  # Add to main layout with stretch
    
    # Register screens
    for screen_type in ScreenFactory.get_available_screen_types():
        screen = ScreenFactory.create_screen(screen_type)
        if screen:
            self.screen_manager.register_screen(screen_type, screen)
            
    # Show initial screen
    self.screen_manager.show_screen('import')
    ``` 

### 2. Import Screen Implementation

- [ ] **Create Import Screen Class**
  - [ ] Create `src/ui/screens/import_screen.py` with the following content:
    ```python
    # src/ui/screens/import_screen.py
    from typing import Dict, Any, Optional, List
    from pathlib import Path
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFileDialog, QFrame, QSplitter,
        QMessageBox
    )
    from PySide6.QtCore import Qt, Signal, Slot, QSize
    from PySide6.QtGui import QIcon, QPixmap

    from ..widgets.data_table import DataTableWidget
    from ..widgets.file_selector import FileSelectorWidget
    from ...services.data_service import DataService
    from ..base_screen import BaseScreen

    class ImportScreen(BaseScreen):
        """Screen for importing data files."""
        
        # Custom signals
        file_imported = Signal(Path)
        
        def __init__(self, parent=None):
            """
            Initialize the import screen.
            
            Args:
                parent: Optional parent widget
            """
            # Initialize data service
            self.data_service = DataService()
            
            # Initialize base class
            super().__init__(parent)
            
        def _setup_ui(self):
            """Set up the user interface."""
            # Create welcome message
            self.welcome_label = QLabel(
                "Welcome to Total Battle Analyzer",
                alignment=Qt.AlignCenter
            )
            self.welcome_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #D4AF37; margin: 20px;"
            )
            
            # Create instruction label
            self.instruction_label = QLabel(
                "Import data from a CSV file to begin analysis",
                alignment=Qt.AlignCenter
            )
            self.instruction_label.setStyleSheet(
                "font-size: 16px; color: #FFFFFF; margin-bottom: 20px;"
            )
            
            # Create file selector widget
            self.file_selector = FileSelectorWidget(
                title="Select CSV File",
                file_types="CSV Files (*.csv)",
                recent_files_enabled=True
            )
            
            # Create preview area
            self.preview_frame = QFrame()
            self.preview_frame.setFrameShape(QFrame.StyledPanel)
            self.preview_layout = QVBoxLayout(self.preview_frame)
            
            self.preview_header = QLabel("Data Preview")
            self.preview_header.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #D4AF37;"
            )
            
            self.preview_table = DataTableWidget()
            
            self.preview_layout.addWidget(self.preview_header)
            self.preview_layout.addWidget(self.preview_table)
            
            # Create import button
            self.import_button = QPushButton("Import Data")
            self.import_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 10px; border-radius: 5px; min-width: 150px;"
            )
            self.import_button.setEnabled(False)  # Disabled until file is selected
            
            # Create splitter for file selector and preview
            self.splitter = QSplitter(Qt.Vertical)
            self.splitter.addWidget(self.file_selector)
            self.splitter.addWidget(self.preview_frame)
            self.splitter.setSizes([200, 400])  # Initial sizes
            
            # Create button layout
            self.button_layout = QHBoxLayout()
            self.button_layout.addStretch()
            self.button_layout.addWidget(self.import_button)
            self.button_layout.addStretch()
            
            # Add components to main layout
            self.layout.addWidget(self.welcome_label)
            self.layout.addWidget(self.instruction_label)
            self.layout.addWidget(self.splitter, 1)  # Give splitter stretch priority
            self.layout.addLayout(self.button_layout)
            
            # Connect signals
            self.file_selector.file_selected.connect(self._on_file_selected)
            self.import_button.clicked.connect(self._on_import_clicked)
            
        def _on_file_selected(self, file_path: Path) -> None:
            """
            Handle file selection.
            
            Args:
                file_path: Path to the selected file
            """
            if not file_path or not file_path.exists():
                return
                
            # Try to load and preview the file
            try:
                # Load first few rows for preview
                preview_data = self.data_service.load_preview(file_path, max_rows=100)
                
                # Show preview
                self.preview_table.set_data(preview_data)
                
                # Enable import button
                self.import_button.setEnabled(True)
                
                # Store file path
                self._data['file_path'] = file_path
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Preview Error",
                    f"Error loading file preview: {str(e)}"
                )
                self.import_button.setEnabled(False)
            
        def _on_import_clicked(self) -> None:
            """Handle import button click."""
            if 'file_path' not in self._data:
                return
                
            file_path = self._data['file_path']
            
            try:
                # Load the entire file
                data = self.data_service.load_file(file_path)
                
                # Store the data
                self._data['imported_data'] = data
                
                # Emit signals
                self.file_imported.emit(file_path)
                self.data_changed.emit()
                
                # Navigate to the raw data screen
                self.screen_action.emit("navigate", "raw_data")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Error importing file: {str(e)}"
                )
    ```

- [ ] **Implement FileSelectorWidget for Import Screen**
  - [ ] Create `src/ui/widgets/file_selector.py` if not created in Part 2:
    ```python
    # src/ui/widgets/file_selector.py
    from typing import Optional, List, Callable
    from pathlib import Path
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFileDialog, QFrame, QListWidget,
        QListWidgetItem, QSplitter, QLineEdit
    )
    from PySide6.QtCore import Qt, Signal, Slot, QSize
    from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent

    class FileSelectorWidget(QWidget):
        """Widget for selecting files."""
        
        # Custom signals
        file_selected = Signal(Path)
        
        def __init__(
            self,
            parent=None,
            title: str = "Select File",
            file_types: str = "All Files (*.*)",
            recent_files_enabled: bool = True,
            max_recent_files: int = 10
        ):
            """
            Initialize the file selector widget.
            
            Args:
                parent: Optional parent widget
                title: Title displayed in the widget
                file_types: File types filter for file dialog
                recent_files_enabled: Whether to show recent files
                max_recent_files: Maximum number of recent files to display
            """
            super().__init__(parent)
            
            # Store properties
            self.widget_title = title
            self.file_types = file_types
            self.recent_files_enabled = recent_files_enabled
            self.max_recent_files = max_recent_files
            
            # Recent files list
            self.recent_files = []
            
            # Set up UI
            self._setup_ui()
            
            # Set up drag and drop
            self.setAcceptDrops(True)
            
        def _setup_ui(self):
            """Set up the user interface."""
            # Create main layout
            self.layout = QVBoxLayout()
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(self.layout)
            
            # Create header
            self.header = QLabel(self.widget_title)
            self.header.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #D4AF37; padding: 5px;"
            )
            
            # Create file path display
            self.file_path_frame = QFrame()
            self.file_path_frame.setFrameShape(QFrame.StyledPanel)
            self.file_path_frame.setStyleSheet(
                "background-color: #2A374F; border-radius: 5px; padding: 5px;"
            )
            
            self.file_path_layout = QHBoxLayout(self.file_path_frame)
            self.file_path_layout.setContentsMargins(5, 5, 5, 5)
            
            self.file_path_label = QLabel("No file selected")
            self.file_path_label.setStyleSheet("color: #AAAAAA;")
            
            self.browse_button = QPushButton("Browse")
            self.browse_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 5px; border-radius: 3px; min-width: 80px;"
            )
            
            self.file_path_layout.addWidget(self.file_path_label, 1)
            self.file_path_layout.addWidget(self.browse_button)
            
            # Create recent files list if enabled
            if self.recent_files_enabled:
                self.recent_files_frame = QFrame()
                self.recent_files_frame.setFrameShape(QFrame.StyledPanel)
                self.recent_files_frame.setStyleSheet(
                    "background-color: #2A374F; border-radius: 5px; margin-top: 10px;"
                )
                
                self.recent_files_layout = QVBoxLayout(self.recent_files_frame)
                
                self.recent_files_header = QLabel("Recent Files")
                self.recent_files_header.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #D4AF37; padding: 5px;"
                )
                
                self.recent_files_list = QListWidget()
                self.recent_files_list.setStyleSheet(
                    "background-color: #1A2742; border: none; color: #FFFFFF;"
                )
                
                self.recent_files_layout.addWidget(self.recent_files_header)
                self.recent_files_layout.addWidget(self.recent_files_list)
            
            # Add components to main layout
            self.layout.addWidget(self.header)
            self.layout.addWidget(self.file_path_frame)
            
            if self.recent_files_enabled:
                self.layout.addWidget(self.recent_files_frame, 1)  # Give stretch priority
            
            # Connect signals
            self.browse_button.clicked.connect(self._on_browse_clicked)
            
            if self.recent_files_enabled:
                self.recent_files_list.itemClicked.connect(self._on_recent_file_clicked)
            
        def _on_browse_clicked(self):
            """Handle browse button click."""
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.widget_title,
                str(Path.home()),
                self.file_types
            )
            
            if file_path:
                self._select_file(Path(file_path))
        
        def _on_recent_file_clicked(self, item: QListWidgetItem):
            """
            Handle recent file selection.
            
            Args:
                item: Selected item in the recent files list
            """
            file_path = item.data(Qt.UserRole)
            if file_path and Path(file_path).exists():
                self._select_file(Path(file_path))
            else:
                # Remove non-existent file from the list
                self.remove_recent_file(Path(file_path))
                self._update_recent_files_list()
        
        def _select_file(self, file_path: Path):
            """
            Select a file and update the UI.
            
            Args:
                file_path: Path to the selected file
            """
            if not file_path.exists():
                return
                
            # Update file path label
            self.file_path_label.setText(file_path.name)
            self.file_path_label.setStyleSheet("color: #FFFFFF;")
            
            # Add to recent files
            if self.recent_files_enabled:
                self.add_recent_file(file_path)
                
            # Emit signal
            self.file_selected.emit(file_path)
        
        def add_recent_file(self, file_path: Path):
            """
            Add a file to the recent files list.
            
            Args:
                file_path: Path to add to recent files
            """
            # Convert to string for storage
            path_str = str(file_path)
            
            # Remove if already in list (to avoid duplicates)
            if path_str in self.recent_files:
                self.recent_files.remove(path_str)
                
            # Add to the beginning of the list
            self.recent_files.insert(0, path_str)
            
            # Trim list to max size
            self.recent_files = self.recent_files[:self.max_recent_files]
            
            # Update the UI
            self._update_recent_files_list()
        
        def remove_recent_file(self, file_path: Path):
            """
            Remove a file from the recent files list.
            
            Args:
                file_path: Path to remove from recent files
            """
            path_str = str(file_path)
            if path_str in self.recent_files:
                self.recent_files.remove(path_str)
                self._update_recent_files_list()
        
        def _update_recent_files_list(self):
            """Update the recent files list widget."""
            if not self.recent_files_enabled:
                return
                
            # Clear the list
            self.recent_files_list.clear()
            
            # Add items
            for path_str in self.recent_files:
                path = Path(path_str)
                if path.exists():
                    item = QListWidgetItem(path.name)
                    item.setData(Qt.UserRole, path_str)
                    self.recent_files_list.addItem(item)
        
        def clear_recent_files(self):
            """Clear the recent files list."""
            self.recent_files = []
            self._update_recent_files_list()
        
        def set_recent_files(self, files: List[str]):
            """
            Set the recent files list.
            
            Args:
                files: List of file paths as strings
            """
            self.recent_files = files[:self.max_recent_files]
            self._update_recent_files_list()
        
        def get_recent_files(self) -> List[str]:
            """
            Get the recent files list.
            
            Returns:
                List of file paths as strings
            """
            return self.recent_files.copy()
            
        # Drag and drop support
        def dragEnterEvent(self, event: QDragEnterEvent):
            """
            Handle drag enter events.
            
            Args:
                event: Drag enter event
            """
            # Accept only if the drag contains URLs (files)
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
        
        def dropEvent(self, event: QDropEvent):
            """
            Handle drop events.
            
            Args:
                event: Drop event
            """
            # Process only the first file
            urls = event.mimeData().urls()
            if urls:
                file_path = Path(urls[0].toLocalFile())
                if file_path.exists() and file_path.is_file():
                    self._select_file(file_path)
    ```

### 3. Raw Data Screen Implementation

- [ ] **Create Raw Data Screen Class**
  - [ ] Create `src/ui/screens/raw_data_screen.py` with the following content:
    ```python
    # src/ui/screens/raw_data_screen.py
    from typing import Dict, Any, Optional, List
    from pathlib import Path
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QSplitter, QCheckBox,
        QComboBox, QDateEdit, QListWidget, QMessageBox,
        QScrollArea
    )
    from PySide6.QtCore import Qt, Signal, Slot, QDate

    from ..widgets.data_table import DataTableWidget
    from ...services.data_service import DataService
    from ..base_screen import BaseScreen

    class RawDataScreen(BaseScreen):
        """Screen for viewing and filtering raw data."""
        
        def __init__(self, parent=None):
            """
            Initialize the raw data screen.
            
            Args:
                parent: Optional parent widget
            """
            # Initialize data service
            self.data_service = DataService()
            
            # Initialize base class
            super().__init__(parent)
            
        def _setup_ui(self):
            """Set up the user interface."""
            # Create header
            self.header = QLabel("Raw Data")
            self.header.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #D4AF37; margin: 10px;"
            )
            
            # Create filter panel
            self.filter_panel = QFrame()
            self.filter_panel.setFrameShape(QFrame.StyledPanel)
            self.filter_panel.setStyleSheet(
                "background-color: #2A374F; border-radius: 5px; padding: 10px;"
            )
            self.filter_panel.setMaximumWidth(300)
            
            self.filter_layout = QVBoxLayout(self.filter_panel)
            
            # Create filter components
            self.filter_header = QLabel("Filters")
            self.filter_header.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #D4AF37; padding: 5px;"
            )
            
            # Date range filter
            self.date_filter_frame = QFrame()
            self.date_filter_layout = QVBoxLayout(self.date_filter_frame)
            
            self.date_filter_label = QLabel("Date Range")
            self.date_filter_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
            
            self.date_filter_enabled = QCheckBox("Enable Date Filter")
            self.date_filter_enabled.setStyleSheet("color: #FFFFFF;")
            
            self.date_range_layout = QHBoxLayout()
            
            self.start_date_label = QLabel("From:")
            self.start_date_label.setStyleSheet("color: #FFFFFF;")
            self.start_date = QDateEdit()
            self.start_date.setCalendarPopup(True)
            self.start_date.setEnabled(False)
            
            self.end_date_label = QLabel("To:")
            self.end_date_label.setStyleSheet("color: #FFFFFF;")
            self.end_date = QDateEdit()
            self.end_date.setCalendarPopup(True)
            self.end_date.setEnabled(False)
            
            self.date_range_layout.addWidget(self.start_date_label)
            self.date_range_layout.addWidget(self.start_date)
            self.date_range_layout.addWidget(self.end_date_label)
            self.date_range_layout.addWidget(self.end_date)
            
            self.date_filter_layout.addWidget(self.date_filter_label)
            self.date_filter_layout.addWidget(self.date_filter_enabled)
            self.date_filter_layout.addLayout(self.date_range_layout)
            
            # Column filters
            self.column_filter_frame = QFrame()
            self.column_filter_layout = QVBoxLayout(self.column_filter_frame)
            
            self.column_filter_label = QLabel("Column Filters")
            self.column_filter_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
            
            self.column_selector_layout = QHBoxLayout()
            
            self.column_selector_label = QLabel("Column:")
            self.column_selector_label.setStyleSheet("color: #FFFFFF;")
            
            self.column_selector = QComboBox()
            self.column_selector.setStyleSheet(
                "background-color: #1A2742; color: #FFFFFF; padding: 5px;"
            )
            
            self.column_selector_layout.addWidget(self.column_selector_label)
            self.column_selector_layout.addWidget(self.column_selector, 1)
            
            self.value_filter_enabled = QCheckBox("Select specific values")
            self.value_filter_enabled.setStyleSheet("color: #FFFFFF;")
            
            self.value_list = QListWidget()
            self.value_list.setStyleSheet(
                "background-color: #1A2742; color: #FFFFFF; selection-background-color: #D4AF37;"
            )
            self.value_list.setSelectionMode(QListWidget.MultiSelection)
            self.value_list.setEnabled(False)
            
            self.value_list_buttons_layout = QHBoxLayout()
            
            self.select_all_button = QPushButton("Select All")
            self.select_all_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 5px; border-radius: 3px;"
            )
            self.select_all_button.setEnabled(False)
            
            self.deselect_all_button = QPushButton("Deselect All")
            self.deselect_all_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 5px; border-radius: 3px;"
            )
            self.deselect_all_button.setEnabled(False)
            
            self.value_list_buttons_layout.addWidget(self.select_all_button)
            self.value_list_buttons_layout.addWidget(self.deselect_all_button)
            
            self.column_filter_layout.addWidget(self.column_filter_label)
            self.column_filter_layout.addLayout(self.column_selector_layout)
            self.column_filter_layout.addWidget(self.value_filter_enabled)
            self.column_filter_layout.addWidget(self.value_list)
            self.column_filter_layout.addLayout(self.value_list_buttons_layout)
            
            # Apply and Reset buttons
            self.filter_buttons_layout = QHBoxLayout()
            
            self.apply_filter_button = QPushButton("Apply Filters")
            self.apply_filter_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 8px; border-radius: 4px;"
            )
            
            self.reset_filter_button = QPushButton("Reset Filters")
            self.reset_filter_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 8px; border-radius: 4px;"
            )
            
            self.filter_buttons_layout.addWidget(self.apply_filter_button)
            self.filter_buttons_layout.addWidget(self.reset_filter_button)
            
            # Export button
            self.export_button = QPushButton("Export Data")
            self.export_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 8px; border-radius: 4px; margin-top: 10px;"
            )
            
            # Add components to filter layout
            self.filter_layout.addWidget(self.filter_header)
            self.filter_layout.addWidget(self.date_filter_frame)
            self.filter_layout.addWidget(self.column_filter_frame)
            self.filter_layout.addLayout(self.filter_buttons_layout)
            self.filter_layout.addWidget(self.export_button)
            self.filter_layout.addStretch()
            
            # Create data table
            self.data_table = DataTableWidget()
            
            # Create main content area with splitter
            self.splitter = QSplitter(Qt.Horizontal)
            self.splitter.addWidget(self.filter_panel)
            self.splitter.addWidget(self.data_table)
            self.splitter.setSizes([300, 700])  # Initial sizes
            
            # Add components to main layout
            self.layout.addWidget(self.header)
            self.layout.addWidget(self.splitter, 1)  # Give splitter stretch priority
            
            # Connect signals
            self.date_filter_enabled.toggled.connect(self._on_date_filter_toggled)
            self.column_selector.currentIndexChanged.connect(self._on_column_selected)
            self.value_filter_enabled.toggled.connect(self._on_value_filter_toggled)
            self.select_all_button.clicked.connect(self._on_select_all_clicked)
            self.deselect_all_button.clicked.connect(self._on_deselect_all_clicked)
            self.apply_filter_button.clicked.connect(self._on_apply_filter_clicked)
            self.reset_filter_button.clicked.connect(self._on_reset_filter_clicked)
            self.export_button.clicked.connect(self._on_export_clicked)
            
        def load_data(self, data: Dict[str, Any]) -> None:
            """
            Load data into the screen.
            
            Args:
                data: Dictionary containing the data to load
            """
            super().load_data(data)
            
            # Check if we have raw data
            if 'raw_data' in self._data:
                # Apply data to table
                self.data_table.set_data(self._data['raw_data'])
                
                # Update column selector
                self._update_column_selector()
                
                # Update date range
                self._update_date_range()
        
        def _update_ui(self) -> None:
            """Update the UI with the current data."""
            # Update data table if we have raw data
            if 'raw_data' in self._data:
                self.data_table.set_data(self._data['raw_data'])
        
        def _update_column_selector(self) -> None:
            """Update the column selector with current data columns."""
            if 'raw_data' not in self._data or self._data['raw_data'].empty:
                return
                
            # Block signals during update
            self.column_selector.blockSignals(True)
            
            # Clear current items
            self.column_selector.clear()
            
            # Add columns
            for column in self._data['raw_data'].columns:
                self.column_selector.addItem(column)
                
            # Unblock signals
            self.column_selector.blockSignals(False)
            
            # Select first item and trigger update
            if self.column_selector.count() > 0:
                self.column_selector.setCurrentIndex(0)
                self._on_column_selected(0)
        
        def _update_date_range(self) -> None:
            """Update the date range controls with data min/max dates."""
            if 'raw_data' not in self._data or self._data['raw_data'].empty:
                return
                
            # Check if we have a DATE column
            if 'DATE' in self._data['raw_data'].columns:
                try:
                    # Get min and max dates
                    date_series = pd.to_datetime(self._data['raw_data']['DATE'])
                    min_date = date_series.min()
                    max_date = date_series.max()
                    
                    # Set date range
                    self.start_date.setDate(QDate(min_date.year, min_date.month, min_date.day))
                    self.end_date.setDate(QDate(max_date.year, max_date.month, max_date.day))
                    
                except Exception as e:
                    print(f"Error setting date range: {e}")
        
        def _on_date_filter_toggled(self, enabled: bool) -> None:
            """
            Handle date filter checkbox toggled.
            
            Args:
                enabled: Whether the date filter is enabled
            """
            self.start_date.setEnabled(enabled)
            self.end_date.setEnabled(enabled)
        
        def _on_column_selected(self, index: int) -> None:
            """
            Handle column selection change.
            
            Args:
                index: Index of the selected column
            """
            if index < 0 or 'raw_data' not in self._data or self._data['raw_data'].empty:
                return
                
            # Get selected column name
            column_name = self.column_selector.currentText()
            
            # Update value list with unique values from the column
            self._update_value_list(column_name)
        
        def _update_value_list(self, column_name: str) -> None:
            """
            Update the value list with unique values from the selected column.
            
            Args:
                column_name: Name of the column to get values from
            """
            if 'raw_data' not in self._data or self._data['raw_data'].empty:
                return
                
            # Clear current items
            self.value_list.clear()
            
            # Get unique values sorted
            unique_values = sorted(self._data['raw_data'][column_name].unique())
            
            # Add items
            for value in unique_values:
                self.value_list.addItem(str(value))
                
            # Select all items by default
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(True)
        
        def _on_value_filter_toggled(self, enabled: bool) -> None:
            """
            Handle value filter checkbox toggled.
            
            Args:
                enabled: Whether the value filter is enabled
            """
            self.value_list.setEnabled(enabled)
            self.select_all_button.setEnabled(enabled)
            self.deselect_all_button.setEnabled(enabled)
        
        def _on_select_all_clicked(self) -> None:
            """Handle select all button click."""
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(True)
        
        def _on_deselect_all_clicked(self) -> None:
            """Handle deselect all button click."""
            for i in range(self.value_list.count()):
                self.value_list.item(i).setSelected(False)
        
        def _on_apply_filter_clicked(self) -> None:
            """Handle apply filter button click."""
            if 'raw_data' not in self._data or self._data['raw_data'].empty:
                return
                
            # Get original data
            df = self._data['raw_data'].copy()
            
            # Apply date filter if enabled
            if self.date_filter_enabled.isChecked() and 'DATE' in df.columns:
                try:
                    # Convert dates
                    start_date = self.start_date.date().toString("yyyy-MM-dd")
                    end_date = self.end_date.date().toString("yyyy-MM-dd")
                    
                    # Filter by date range
                    df = df[(df['DATE'] >= start_date) & (df['DATE'] <= end_date)]
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Date Filter Error",
                        f"Error applying date filter: {str(e)}"
                    )
            
            # Apply column value filter if enabled
            if self.value_filter_enabled.isChecked():
                # Get selected column
                column_name = self.column_selector.currentText()
                
                # Get selected values
                selected_values = [item.text() for item in self.value_list.selectedItems()]
                
                # Filter by selected values
                if selected_values:
                    df = df[df[column_name].astype(str).isin(selected_values)]
            
            # Update table with filtered data
            self.data_table.set_data(df)
        
        def _on_reset_filter_clicked(self) -> None:
            """Handle reset filter button click."""
            # Reset date filter
            self.date_filter_enabled.setChecked(False)
            
            # Reset value filter
            self.value_filter_enabled.setChecked(False)
            
            # Reset value list selection
            self._on_select_all_clicked()
            
            # Reset table to show all data
            if 'raw_data' in self._data:
                self.data_table.set_data(self._data['raw_data'])
        
        def _on_export_clicked(self) -> None:
            """Handle export button click."""
            # Get current table data
            df = self.data_table.get_data()
            
            if df.empty:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    "No data to export"
                )
                return
                
            # Get file path for saving
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Data",
                str(Path.home() / "exported_data.csv"),
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
                
            try:
                # Export to CSV
                self.data_service.export_data(df, Path(file_path))
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data exported to {file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting data: {str(e)}"
                )
    ```

- [ ] **Update Data Service For Raw Data Screen**
  - [ ] Create or update `src/services/data_service.py` to support data operations:
    ```python
    # src/services/data_service.py
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path
    import pandas as pd
    import numpy as np
    import os
    import csv

    class DataService:
        """Service for data operations."""
        
        def __init__(self):
            """Initialize the data service."""
            pass
            
        def load_preview(self, file_path: Path, max_rows: int = 100) -> pd.DataFrame:
            """
            Load a preview of a CSV file.
            
            Args:
                file_path: Path to the CSV file
                max_rows: Maximum number of rows to load
                
            Returns:
                DataFrame containing the preview data
                
            Raises:
                FileNotFoundError: If the file does not exist
                ValueError: If the file is not a CSV file
                Exception: For other errors during loading
            """
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Check if file is a CSV
            if file_path.suffix.lower() != '.csv':
                raise ValueError(f"File is not a CSV file: {file_path}")
                
            try:
                # Try UTF-8 encoding first
                df = pd.read_csv(file_path, nrows=max_rows)
                return df
            except UnicodeDecodeError:
                # Try with different encodings
                try:
                    df = pd.read_csv(file_path, nrows=max_rows, encoding='latin-1')
                    return df
                except Exception:
                    try:
                        df = pd.read_csv(file_path, nrows=max_rows, encoding='cp1252')
                        return df
                    except Exception as e:
                        raise Exception(f"Error loading CSV file: {str(e)}")
            except Exception as e:
                raise Exception(f"Error loading CSV file: {str(e)}")
                
        def load_file(self, file_path: Path) -> pd.DataFrame:
            """
            Load a CSV file.
            
            Args:
                file_path: Path to the CSV file
                
            Returns:
                DataFrame containing the data
                
            Raises:
                FileNotFoundError: If the file does not exist
                ValueError: If the file is not a CSV file
                Exception: For other errors during loading
            """
            # Use the same loading logic as preview but without row limit
            return self.load_preview(file_path, max_rows=None)
            
        def export_data(self, data: pd.DataFrame, file_path: Path) -> None:
            """
            Export data to a file.
            
            Args:
                data: DataFrame to export
                file_path: Path to save the file to
                
            Raises:
                ValueError: If the data is empty
                Exception: For other errors during export
            """
            if data.empty:
                raise ValueError("No data to export")
                
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Export to CSV with UTF-8 encoding
                data.to_csv(file_path, index=False, encoding='utf-8-sig')
            except Exception as e:
                raise Exception(f"Error exporting data: {str(e)}")
    
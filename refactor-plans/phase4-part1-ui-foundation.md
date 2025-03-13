# Total Battle Analyzer Refactoring Plan: Phase 4 - Part 1
## UI Foundation

This document details the implementation of the UI foundation for the Total Battle Analyzer application as part of Phase 4 refactoring.

### 1. Setup and Preparation

- [ ] **Directory Structure Verification**
  - [ ] Ensure the `src/ui` directory exists with appropriate subdirectories:
    ```bash
    mkdir -p src/ui/main
    mkdir -p src/ui/widgets
    mkdir -p src/ui/dialogs
    mkdir -p src/ui/styles
    mkdir -p src/ui/assets
    ```
  - [ ] Create necessary `__init__.py` files:
    ```bash
    touch src/ui/__init__.py
    touch src/ui/main/__init__.py
    touch src/ui/widgets/__init__.py
    touch src/ui/dialogs/__init__.py
    touch src/ui/styles/__init__.py
    ```

- [ ] **Dependency Verification**
  - [ ] Ensure all required UI libraries are installed:
    ```bash
    uv add pyside6 qdarkstyle
    ```
  - [ ] Document any additional UI dependencies that may be needed

### 2. Application Theme and Styling

- [ ] **Create Theme Manager**
  - [ ] Create `src/ui/styles/theme_manager.py` with the following content:
    ```python
    # src/ui/styles/theme_manager.py
    from enum import Enum
    from typing import Dict, Optional, Union
    from pathlib import Path
    import json
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication
    import qdarkstyle

    class Theme(Enum):
        """Application themes."""
        LIGHT = "light"
        DARK = "dark"
        BLUE = "blue"
        CUSTOM = "custom"

    class ThemeManager:
        """Manager for application theming and styling."""
        
        def __init__(self, app: QApplication):
            """
            Initialize the theme manager.
            
            Args:
                app: The QApplication instance
            """
            self.app = app
            self._current_theme = Theme.DARK
            self._custom_stylesheet = ""
            self._color_schemes = {
                Theme.LIGHT: {
                    'background': '#F0F0F0',
                    'foreground': '#333333',
                    'primary': '#5991C4',
                    'secondary': '#6EC1A7',
                    'accent': '#D4AF37',
                    'error': '#D46A5F',
                    'warning': '#F0C75A',
                    'success': '#6EC1A7',
                    'border': '#CCCCCC',
                    'highlight': '#D4AF37',
                },
                Theme.DARK: {
                    'background': '#1A2742',
                    'foreground': '#FFFFFF',
                    'primary': '#5991C4',
                    'secondary': '#6EC1A7',
                    'accent': '#D4AF37',
                    'error': '#D46A5F',
                    'warning': '#F0C75A',
                    'success': '#6EC1A7',
                    'border': '#2A3F5F',
                    'highlight': '#D4AF37',
                },
                Theme.BLUE: {
                    'background': '#0E1629',
                    'foreground': '#FFFFFF',
                    'primary': '#5991C4',
                    'secondary': '#6EC1A7',
                    'accent': '#D4AF37',
                    'error': '#D46A5F',
                    'warning': '#F0C75A',
                    'success': '#6EC1A7',
                    'border': '#2A3F5F',
                    'highlight': '#D4AF37',
                }
            }
            
        def apply_theme(self, theme: Union[Theme, str]) -> None:
            """
            Apply a theme to the application.
            
            Args:
                theme: The theme to apply
            """
            # Convert string to Theme enum if needed
            if isinstance(theme, str):
                try:
                    theme = Theme(theme.lower())
                except ValueError:
                    theme = Theme.DARK
                    
            # Set current theme
            self._current_theme = theme
            
            # Apply the theme
            if theme == Theme.LIGHT:
                self._apply_light_theme()
            elif theme == Theme.DARK:
                self._apply_dark_theme()
            elif theme == Theme.BLUE:
                self._apply_blue_theme()
            elif theme == Theme.CUSTOM and self._custom_stylesheet:
                self.app.setStyleSheet(self._custom_stylesheet)
                
            # Apply additional styling
            self._apply_common_styling()
            
        def get_color(self, color_key: str) -> QColor:
            """
            Get a color from the current theme.
            
            Args:
                color_key: The color key
                
            Returns:
                QColor object
            """
            if self._current_theme in self._color_schemes and color_key in self._color_schemes[self._current_theme]:
                color_hex = self._color_schemes[self._current_theme][color_key]
                return QColor(color_hex)
            return QColor("#FFFFFF")  # Default to white
            
        def set_custom_stylesheet(self, stylesheet: str) -> None:
            """
            Set a custom stylesheet.
            
            Args:
                stylesheet: The CSS stylesheet
            """
            self._custom_stylesheet = stylesheet
            if self._current_theme == Theme.CUSTOM:
                self.app.setStyleSheet(stylesheet)
                
        def load_custom_theme(self, theme_file: Union[str, Path]) -> bool:
            """
            Load a custom theme from a file.
            
            Args:
                theme_file: Path to theme file (JSON)
                
            Returns:
                True if successful, False otherwise
            """
            try:
                # Ensure theme_file is a Path object
                if isinstance(theme_file, str):
                    theme_file = Path(theme_file)
                    
                # Load the theme file
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                    
                # Update color scheme
                if 'colors' in theme_data:
                    self._color_schemes[Theme.CUSTOM] = theme_data['colors']
                    
                # Update stylesheet if present
                if 'stylesheet' in theme_data:
                    self._custom_stylesheet = theme_data['stylesheet']
                    
                return True
                
            except Exception as e:
                print(f"Error loading custom theme: {str(e)}")
                return False
                
        def _apply_light_theme(self) -> None:
            """Apply the light theme."""
            # Clear any existing stylesheet
            self.app.setStyleSheet("")
            
            # Create and set light palette
            palette = QPalette()
            # Set up light palette colors...
            self.app.setPalette(palette)
            
        def _apply_dark_theme(self) -> None:
            """Apply the dark theme."""
            # Apply qdarkstyle
            self.app.setStyleSheet(qdarkstyle.load_stylesheet())
            
        def _apply_blue_theme(self) -> None:
            """Apply the blue theme."""
            # Apply custom blue theme
            stylesheet = """
            QWidget {
                background-color: #0E1629;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #5991C4;
                color: #FFFFFF;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #6BA0D3;
            }
            QPushButton:pressed {
                background-color: #4A82B5;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
                background-color: #1A2742;
                border: 1px solid #2A3F5F;
                border-radius: 3px;
                color: #FFFFFF;
                padding: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #2A3F5F;
                background-color: #1A2742;
            }
            QTabBar::tab {
                background-color: #0E1629;
                color: #FFFFFF;
                padding: 8px 12px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
            }
            QTabBar::tab:selected {
                background-color: #1A2742;
                border-bottom: 2px solid #D4AF37;
            }
            QTableView, QTreeView, QListView {
                background-color: #1A2742;
                alternate-background-color: #192236;
                border: 1px solid #2A3F5F;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #0E1629;
                color: #D4AF37;
                padding: 5px;
                border: 1px solid #2A3F5F;
            }
            """
            self.app.setStyleSheet(stylesheet)
            
        def _apply_common_styling(self) -> None:
            """Apply common styling across all themes."""
            # Add any common styling elements here
            pass
    ```

- [ ] **Create Application Stylesheet**
  - [ ] Create `src/ui/styles/app_style.qss` for custom styles

### 3. Main Application Window

- [ ] **Create Main Window Base**
  - [ ] Create `src/ui/main/main_window.py` with the following content:
    ```python
    # src/ui/main/main_window.py
    from typing import Dict, Any, Optional, List, Callable
    from pathlib import Path
    import os
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QLabel, QPushButton, QTabWidget, QStatusBar,
        QToolBar, QMenuBar, QMenu, QAction, QMessageBox,
        QFileDialog
    )
    from PySide6.QtCore import Qt, Signal, Slot, QSize
    from PySide6.QtGui import QIcon, QKeySequence

    class MainWindow(QMainWindow):
        """Main application window."""
        
        def __init__(self, parent=None):
            """
            Initialize the main window.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Set window properties
            self.setWindowTitle("Total Battle Analyzer")
            self.setMinimumSize(1000, 700)
            
            # Initialize UI components
            self._init_ui()
            self._create_menu_bar()
            self._create_tool_bar()
            self._create_status_bar()
            self._create_central_widget()
            self._create_tabs()
            
            # Connect signals and slots
            self._connect_signals()
            
        def _init_ui(self) -> None:
            """Initialize UI properties."""
            # Set window icon
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                
        def _create_menu_bar(self) -> None:
            """Create the menu bar."""
            self.menu_bar = self.menuBar()
            
            # File menu
            self.file_menu = self.menu_bar.addMenu("&File")
            
            # Create actions
            self.action_open = QAction("&Open Data", self)
            self.action_open.setShortcut(QKeySequence("Ctrl+O"))
            self.action_save = QAction("&Save Data", self)
            self.action_save.setShortcut(QKeySequence("Ctrl+S"))
            self.action_export = QAction("&Export Results", self)
            self.action_export.setShortcut(QKeySequence("Ctrl+E"))
            self.action_preferences = QAction("&Preferences", self)
            self.action_exit = QAction("E&xit", self)
            self.action_exit.setShortcut(QKeySequence("Ctrl+Q"))
            
            # Add actions to file menu
            self.file_menu.addAction(self.action_open)
            self.file_menu.addAction(self.action_save)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.action_export)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.action_preferences)
            self.file_menu.addSeparator()
            self.file_menu.addAction(self.action_exit)
            
            # Analysis menu
            self.analysis_menu = self.menu_bar.addMenu("&Analysis")
            
            # Create actions
            self.action_run_analysis = QAction("&Run Analysis", self)
            self.action_run_analysis.setShortcut(QKeySequence("F5"))
            self.action_stop_analysis = QAction("&Stop Analysis", self)
            self.action_view_results = QAction("&View Results", self)
            
            # Add actions to analysis menu
            self.analysis_menu.addAction(self.action_run_analysis)
            self.analysis_menu.addAction(self.action_stop_analysis)
            self.analysis_menu.addSeparator()
            self.analysis_menu.addAction(self.action_view_results)
            
            # Help menu
            self.help_menu = self.menu_bar.addMenu("&Help")
            
            # Create actions
            self.action_documentation = QAction("&Documentation", self)
            self.action_documentation.setShortcut(QKeySequence("F1"))
            self.action_about = QAction("&About", self)
            
            # Add actions to help menu
            self.help_menu.addAction(self.action_documentation)
            self.help_menu.addSeparator()
            self.help_menu.addAction(self.action_about)
            
        def _create_tool_bar(self) -> None:
            """Create the tool bar."""
            self.tool_bar = QToolBar("Main Toolbar")
            self.tool_bar.setMovable(False)
            self.tool_bar.setIconSize(QSize(24, 24))
            self.addToolBar(self.tool_bar)
            
            # Add actions to toolbar
            self.tool_bar.addAction(self.action_open)
            self.tool_bar.addAction(self.action_save)
            self.tool_bar.addSeparator()
            self.tool_bar.addAction(self.action_run_analysis)
            self.tool_bar.addAction(self.action_view_results)
            
        def _create_status_bar(self) -> None:
            """Create the status bar."""
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # Add status label
            self.status_label = QLabel("Ready")
            self.status_bar.addWidget(self.status_label)
            
            # Add progress indicator (to be implemented)
            
        def _create_central_widget(self) -> None:
            """Create the central widget."""
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            
            # Create main layout
            self.main_layout = QVBoxLayout()
            self.central_widget.setLayout(self.main_layout)
            
        def _create_tabs(self) -> None:
            """Create the main tabs."""
            self.tab_widget = QTabWidget()
            self.main_layout.addWidget(self.tab_widget)
            
            # Create placeholder tabs
            self.data_tab = QWidget()
            self.analysis_tab = QWidget()
            self.results_tab = QWidget()
            self.reports_tab = QWidget()
            
            # Add tabs to the tab widget
            self.tab_widget.addTab(self.data_tab, "Data")
            self.tab_widget.addTab(self.analysis_tab, "Analysis")
            self.tab_widget.addTab(self.results_tab, "Results")
            self.tab_widget.addTab(self.reports_tab, "Reports")
            
            # Set up tab layouts
            self.data_tab_layout = QVBoxLayout()
            self.data_tab.setLayout(self.data_tab_layout)
            
            self.analysis_tab_layout = QVBoxLayout()
            self.analysis_tab.setLayout(self.analysis_tab_layout)
            
            self.results_tab_layout = QVBoxLayout()
            self.results_tab.setLayout(self.results_tab_layout)
            
            self.reports_tab_layout = QVBoxLayout()
            self.reports_tab.setLayout(self.reports_tab_layout)
            
        def _connect_signals(self) -> None:
            """Connect signals and slots."""
            # Connect menu actions
            self.action_exit.triggered.connect(self.close)
            self.action_about.triggered.connect(self._show_about_dialog)
            
        @Slot()
        def _show_about_dialog(self) -> None:
            """Show the about dialog."""
            QMessageBox.about(
                self,
                "About Total Battle Analyzer",
                "Total Battle Analyzer v1.0\n\n"
                "A data analysis tool for Total Battle game data.\n\n"
                "© 2023 Total Battle Analyzer Team"
            )
            
        def show_status_message(self, message: str, timeout: int = 0) -> None:
            """
            Show a message in the status bar.
            
            Args:
                message: The message to show
                timeout: Time in milliseconds to show the message, 0 for indefinite
            """
            self.status_bar.showMessage(message, timeout)
            self.status_label.setText(message)
            
        def closeEvent(self, event) -> None:
            """
            Handle window close event.
            
            Args:
                event: Close event
            """
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Exit",
                "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
    ```

### 4. Navigation System

- [ ] **Create Navigation Framework**
  - [ ] Create `src/ui/main/navigator.py` with the following content:
    ```python
    # src/ui/main/navigator.py
    from typing import Dict, Any, Optional, List, Callable
    from enum import Enum, auto
    from PySide6.QtWidgets import QWidget, QTabWidget

    class NavigationDestination(Enum):
        """Navigation destinations within the application."""
        DATA = auto()
        ANALYSIS = auto()
        RESULTS = auto()
        REPORTS = auto()
        SETTINGS = auto()

    class Navigator:
        """Navigation controller for the application."""
        
        def __init__(self, tab_widget: QTabWidget):
            """
            Initialize the navigator.
            
            Args:
                tab_widget: The main tab widget
            """
            self.tab_widget = tab_widget
            self._page_index_map = {}
            self._initialize_mapping()
            
        def _initialize_mapping(self) -> None:
            """Initialize the page index mapping."""
            # Map enum values to tab indices
            for i in range(self.tab_widget.count()):
                tab_text = self.tab_widget.tabText(i)
                
                if tab_text.upper() == "DATA":
                    self._page_index_map[NavigationDestination.DATA] = i
                elif tab_text.upper() == "ANALYSIS":
                    self._page_index_map[NavigationDestination.ANALYSIS] = i
                elif tab_text.upper() == "RESULTS":
                    self._page_index_map[NavigationDestination.RESULTS] = i
                elif tab_text.upper() == "REPORTS":
                    self._page_index_map[NavigationDestination.REPORTS] = i
                    
        def navigate_to(self, destination: NavigationDestination) -> bool:
            """
            Navigate to a specific destination.
            
            Args:
                destination: The destination to navigate to
                
            Returns:
                True if successful, False otherwise
            """
            if destination in self._page_index_map:
                self.tab_widget.setCurrentIndex(self._page_index_map[destination])
                return True
            return False
            
        def register_page(self, destination: NavigationDestination, widget: QWidget, title: str) -> None:
            """
            Register a new page.
            
            Args:
                destination: The navigation destination
                widget: The widget to display
                title: The tab title
            """
            index = self.tab_widget.addTab(widget, title)
            self._page_index_map[destination] = index
            
        def get_current_destination(self) -> Optional[NavigationDestination]:
            """
            Get the current navigation destination.
            
            Returns:
                The current destination or None if not found
            """
            current_index = self.tab_widget.currentIndex()
            
            for destination, index in self._page_index_map.items():
                if index == current_index:
                    return destination
                    
            return None
    ```

### 5. Application Entry Point

- [ ] **Create Application Class**
  - [ ] Create `src/ui/main/application.py` with the following content:
    ```python
    # src/ui/main/application.py
    import sys
    from typing import Dict, Any, Optional, List
    from pathlib import Path
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings
    from app.services.service_registry import ServiceRegistry
    from app.services.service_provider import ServiceProvider
    from app.integrations import ApplicationIntegration
    from ui.main.main_window import MainWindow
    from ui.styles.theme_manager import ThemeManager, Theme
    
    class Application(QApplication):
        """Main application class."""
        
        def __init__(self, argv: List[str]):
            """
            Initialize the application.
            
            Args:
                argv: Command line arguments
            """
            super().__init__(argv)
            
            # Set application metadata
            self.setApplicationName("TotalBattleAnalyzer")
            self.setApplicationVersion("1.0.0")
            self.setOrganizationName("TotalBattleAnalyzer")
            self.setOrganizationDomain("totalbattleanalyzer.example.com")
            
            # Initialize services
            self._initialize_services()
            
            # Initialize theme manager
            self.theme_manager = ThemeManager(self)
            
            # Load user preferences
            self._load_preferences()
            
            # Create main window
            self.main_window = MainWindow()
            
            # Connect application to services
            self._connect_services()
            
        def _initialize_services(self) -> None:
            """Initialize application services."""
            # Get application directory
            app_dir = Path(__file__).resolve().parent.parent.parent.parent
            
            # Create application integration
            self.app_integration = ApplicationIntegration(app_dir, debug=False)
            
        def _load_preferences(self) -> None:
            """Load user preferences."""
            # Load settings
            settings = QSettings()
            
            # Load theme
            theme_name = settings.value("ui/theme", Theme.DARK.value)
            self.theme_manager.apply_theme(theme_name)
            
            # Load other preferences
            # ...
            
        def _connect_services(self) -> None:
            """Connect application to services."""
            # Connect services to UI
            # ...
            
        def run(self) -> int:
            """
            Run the application.
            
            Returns:
                Exit code
            """
            # Show main window
            self.main_window.show()
            
            # Run event loop
            return self.exec()
            
        def save_preferences(self) -> None:
            """Save user preferences."""
            # Save settings
            settings = QSettings()
            
            # Save theme
            settings.setValue("ui/theme", self.theme_manager._current_theme.value)
            
            # Save other preferences
            # ...
    ```

- [ ] **Create Main Application Entry Point**
  - [ ] Create `src/main.py` with the following content:
    ```python
    # src/main.py
    import sys
    from ui.main.application import Application

    def main():
        """Application entry point."""
        app = Application(sys.argv)
        return app.run()

    if __name__ == "__main__":
        sys.exit(main())
    ```

### 6. Layout Framework

- [ ] **Create Base Layout Widgets**
  - [ ] Create `src/ui/widgets/layouts.py` with layout utilities

### 7. Core Event System

- [ ] **Create Event Bus**
  - [ ] Create `src/ui/main/event_bus.py` with the following content:
    ```python
    # src/ui/main/event_bus.py
    from typing import Dict, Any, Optional, List, Callable
    from enum import Enum, auto
    from PySide6.QtCore import QObject, Signal

    class EventType(Enum):
        """Types of application events."""
        DATA_LOADED = auto()
        DATA_SAVED = auto()
        ANALYSIS_STARTED = auto()
        ANALYSIS_COMPLETED = auto()
        ANALYSIS_FAILED = auto()
        REPORT_GENERATED = auto()
        SETTINGS_CHANGED = auto()
        UI_THEME_CHANGED = auto()

    class EventData:
        """Container for event data."""
        
        def __init__(self, event_type: EventType, data: Optional[Dict[str, Any]] = None):
            """
            Initialize event data.
            
            Args:
                event_type: Type of event
                data: Event data
            """
            self.event_type = event_type
            self.data = data or {}

    class EventBusSignals(QObject):
        """Signal emitter for the event bus."""
        event_emitted = Signal(EventData)

    class EventBus:
        """
        Central event bus for application-wide communication.
        
        This class implements the publish-subscribe pattern for
        decoupled communication between application components.
        """
        
        _instance = None
        
        def __new__(cls):
            """Implement singleton pattern."""
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
            
        def _initialize(self) -> None:
            """Initialize the event bus."""
            self.signals = EventBusSignals()
            self._handlers = {}
            
        def subscribe(self, event_type: EventType, handler: Callable[[EventData], None]) -> None:
            """
            Subscribe to an event.
            
            Args:
                event_type: Type of event to subscribe to
                handler: Function to call when event occurs
            """
            if event_type not in self._handlers:
                self._handlers[event_type] = []
                
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                
        def unsubscribe(self, event_type: EventType, handler: Callable[[EventData], None]) -> None:
            """
            Unsubscribe from an event.
            
            Args:
                event_type: Type of event to unsubscribe from
                handler: Handler to remove
            """
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                
        def publish(self, event_data: EventData) -> None:
            """
            Publish an event.
            
            Args:
                event_data: Event data
            """
            # Emit signal
            self.signals.event_emitted.emit(event_data)
            
            # Call handlers directly
            event_type = event_data.event_type
            if event_type in self._handlers:
                for handler in self._handlers[event_type]:
                    try:
                        handler(event_data)
                    except Exception as e:
                        print(f"Error in event handler: {str(e)}")
    ```

### 8. Documentation

- [ ] **Update UI Documentation**
  - [ ] Add detailed docstrings to all classes and methods
  - [ ] Create examples for common UI patterns
  - [ ] Document theme customization

- [ ] **Create UI Guide**
  - [ ] Create a guide for extending the UI
  - [ ] Include examples of adding new tabs and widgets
  - [ ] Add troubleshooting section for common issues

### 9. Part 1 Validation

- [ ] **Review Implementation**
  - [ ] Verify all required UI foundation components are implemented
  - [ ] Check for proper error handling and robustness
  - [ ] Ensure code quality meets project standards

- [ ] **Test UI Foundation**
  - [ ] Verify main window displays correctly
  - [ ] Test theme switching
  - [ ] Test navigation between tabs
  - [ ] Test event bus functionality

- [ ] **Documentation Verification**
  - [ ] Verify all components are properly documented
  - [ ] Update any outdated documentation
  - [ ] Ensure examples are clear and helpful

### Feedback Request

After completing Part 1 of Phase 4, please provide feedback on the following aspects:

1. Does the UI foundation provide a solid base for building the rest of the application?
2. Is the theming approach flexible enough for customization?
3. Is the navigation system intuitive and easy to use?
4. Does the main window layout meet the requirements for the application?
5. Any suggestions for improvements before proceeding to Part 2? 
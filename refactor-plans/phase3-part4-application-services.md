# Total Battle Analyzer Refactoring Plan: Phase 3 - Part 4
## Application Services

This document details the implementation of application services for the Total Battle Analyzer application as part of Phase 3 refactoring.

### 1. Setup and Preparation

- [ ] **Directory Structure Verification**
  - [ ] Ensure the `src/app/services` directory exists
  - [ ] Create it if missing:
    ```bash
    mkdir -p src/app/services
    ```
  - [ ] Create the `__init__.py` file in the services directory:
    ```bash
    touch src/app/services/__init__.py
    ```

- [ ] **Dependency Verification**
  - [ ] Ensure all required application libraries are installed:
    ```bash
    uv add pyside6 configparser
    ```
  - [ ] Document any additional dependencies that may be needed

### 2. Configuration Service

- [ ] **Create Configuration Service Interface**
  - [ ] Create `src/app/services/config_service.py` with the following content:
    ```python
    # src/app/services/config_service.py
    from abc import ABC, abstractmethod
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path

    class ConfigService(ABC):
        """Interface for configuration management."""
        
        @abstractmethod
        def get_config(self, section: str, key: str, default: Any = None) -> Any:
            """
            Get a configuration value.
            
            Args:
                section: Configuration section
                key: Configuration key
                default: Default value if key not found
                
            Returns:
                Configuration value
            """
            pass
        
        @abstractmethod
        def set_config(self, section: str, key: str, value: Any) -> bool:
            """
            Set a configuration value.
            
            Args:
                section: Configuration section
                key: Configuration key
                value: Value to set
                
            Returns:
                True if successful, False otherwise
            """
            pass
        
        @abstractmethod
        def get_section(self, section: str) -> Dict[str, Any]:
            """
            Get all key-value pairs in a section.
            
            Args:
                section: Configuration section
                
            Returns:
                Dictionary of configuration values
            """
            pass
        
        @abstractmethod
        def save_config(self) -> bool:
            """
            Save configuration to file.
            
            Returns:
                True if successful, False otherwise
            """
            pass
        
        @abstractmethod
        def reset_config(self, section: Optional[str] = None) -> bool:
            """
            Reset configuration to defaults.
            
            Args:
                section: Optional section to reset, if None resets all
                
            Returns:
                True if successful, False otherwise
            """
            pass
    ```

- [ ] **Implement File-Based Configuration Service**
  - [ ] Create `src/app/services/file_config_service.py` with the following content:
    ```python
    # src/app/services/file_config_service.py
    import configparser
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path
    import os
    import json
    from .config_service import ConfigService

    class FileConfigService(ConfigService):
        """Configuration service that uses a file for storage."""
        
        def __init__(
            self,
            config_file: Union[str, Path],
            default_config: Optional[Dict[str, Dict[str, Any]]] = None,
            debug: bool = False
        ):
            """
            Initialize the configuration service.
            
            Args:
                config_file: Path to configuration file
                default_config: Default configuration values
                debug: Whether to enable debug output
            """
            self.debug = debug
            
            # Ensure config_file is a Path object
            if isinstance(config_file, str):
                self.config_file = Path(config_file)
            else:
                self.config_file = config_file
                
            # Initialize default configuration
            self.default_config = default_config or {
                'general': {
                    'data_directory': 'data',
                    'reports_directory': 'reports',
                    'auto_save': True,
                    'debug_mode': False,
                },
                'ui': {
                    'theme': 'dark',
                    'font_size': 12,
                    'show_tooltips': True,
                    'window_width': 1200,
                    'window_height': 800,
                },
                'analysis': {
                    'min_score_threshold': 0,
                    'max_categories': 10,
                    'exclude_outliers': False,
                    'date_range_days': 30,
                },
                'export': {
                    'default_format': 'csv',
                    'include_headers': True,
                    'date_format': '%Y-%m-%d',
                    'chart_dpi': 100,
                }
            }
            
            # Load configuration
            self.config = configparser.ConfigParser()
            self._load_config()
            
        def get_config(self, section: str, key: str, default: Any = None) -> Any:
            """Get a configuration value."""
            try:
                if section in self.config and key in self.config[section]:
                    value = self.config[section][key]
                    
                    # Try to convert to appropriate type
                    if value.lower() in ('true', 'false'):
                        return value.lower() == 'true'
                    
                    try:
                        if '.' in value:
                            return float(value)
                        else:
                            return int(value)
                    except ValueError:
                        # If it's a JSON string, parse it
                        if value.startswith('{') or value.startswith('['):
                            try:
                                return json.loads(value)
                            except json.JSONDecodeError:
                                pass
                        
                        # Otherwise return as string
                        return value
                
                # If not found, check defaults
                if (self.default_config and section in self.default_config and 
                    key in self.default_config[section]):
                    return self.default_config[section][key]
                    
                return default
                
            except Exception as e:
                if self.debug:
                    print(f"Error getting config: {str(e)}")
                return default
                
        def set_config(self, section: str, key: str, value: Any) -> bool:
            """Set a configuration value."""
            try:
                # Ensure section exists
                if section not in self.config:
                    self.config[section] = {}
                    
                # Convert value to string representation
                if isinstance(value, bool):
                    str_value = str(value).lower()
                elif isinstance(value, (dict, list)):
                    str_value = json.dumps(value)
                else:
                    str_value = str(value)
                    
                # Set value
                self.config[section][key] = str_value
                
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error setting config: {str(e)}")
                return False
                
        def get_section(self, section: str) -> Dict[str, Any]:
            """Get all key-value pairs in a section."""
            result = {}
            
            try:
                # Get values from config
                if section in self.config:
                    for key in self.config[section]:
                        result[key] = self.get_config(section, key)
                        
                # Add any missing values from defaults
                if self.default_config and section in self.default_config:
                    for key in self.default_config[section]:
                        if key not in result:
                            result[key] = self.default_config[section][key]
                            
            except Exception as e:
                if self.debug:
                    print(f"Error getting section: {str(e)}")
                    
            return result
            
        def save_config(self) -> bool:
            """Save configuration to file."""
            try:
                # Ensure directory exists
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write config to file
                with open(self.config_file, 'w') as f:
                    self.config.write(f)
                    
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error saving config: {str(e)}")
                return False
                
        def reset_config(self, section: Optional[str] = None) -> bool:
            """Reset configuration to defaults."""
            try:
                if not self.default_config:
                    return False
                    
                if section:
                    # Reset only specified section
                    if section in self.default_config:
                        if section not in self.config:
                            self.config[section] = {}
                            
                        for key, value in self.default_config[section].items():
                            if isinstance(value, bool):
                                self.config[section][key] = str(value).lower()
                            elif isinstance(value, (dict, list)):
                                self.config[section][key] = json.dumps(value)
                            else:
                                self.config[section][key] = str(value)
                else:
                    # Reset all sections
                    for section_name, section_dict in self.default_config.items():
                        if section_name not in self.config:
                            self.config[section_name] = {}
                            
                        for key, value in section_dict.items():
                            if isinstance(value, bool):
                                self.config[section_name][key] = str(value).lower()
                            elif isinstance(value, (dict, list)):
                                self.config[section_name][key] = json.dumps(value)
                            else:
                                self.config[section_name][key] = str(value)
                                
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error resetting config: {str(e)}")
                return False
                
        def _load_config(self) -> None:
            """Load configuration from file."""
            try:
                if self.config_file.exists():
                    # Load from file
                    self.config.read(self.config_file)
                    
                # Ensure all default sections and values exist
                if self.default_config:
                    for section, values in self.default_config.items():
                        if section not in self.config:
                            self.config[section] = {}
                            
                # Save config to ensure file exists
                self.save_config()
                
            except Exception as e:
                if self.debug:
                    print(f"Error loading config: {str(e)}")
                    
                # Reset to defaults
                self.config = configparser.ConfigParser()
                self.reset_config()
    ```

### 3. UI Service Interface

- [ ] **Create UI Service Interface**
  - [ ] Create `src/app/services/ui_service.py` with the following content:
    ```python
    # src/app/services/ui_service.py
    from abc import ABC, abstractmethod
    from typing import Dict, Any, Optional, List, Union, Callable
    from pathlib import Path

    class UIService(ABC):
        """Interface for UI operations."""
        
        @abstractmethod
        def show_message(
            self,
            title: str,
            message: str,
            message_type: str = "info"
        ) -> None:
            """
            Show a message dialog.
            
            Args:
                title: Dialog title
                message: Message text
                message_type: Type of message ('info', 'warning', 'error', 'question')
            """
            pass
        
        @abstractmethod
        def show_file_dialog(
            self,
            dialog_type: str = "open",
            title: str = "Select File",
            directory: Optional[Union[str, Path]] = None,
            file_filter: str = "All Files (*.*)"
        ) -> Optional[str]:
            """
            Show a file dialog.
            
            Args:
                dialog_type: Type of dialog ('open', 'save')
                title: Dialog title
                directory: Starting directory
                file_filter: File filter string
                
            Returns:
                Selected file path or None if cancelled
            """
            pass
        
        @abstractmethod
        def show_directory_dialog(
            self,
            title: str = "Select Directory",
            directory: Optional[Union[str, Path]] = None
        ) -> Optional[str]:
            """
            Show a directory selection dialog.
            
            Args:
                title: Dialog title
                directory: Starting directory
                
            Returns:
                Selected directory path or None if cancelled
            """
            pass
        
        @abstractmethod
        def show_progress(
            self,
            value: int,
            maximum: int,
            message: Optional[str] = None
        ) -> None:
            """
            Update progress indicator.
            
            Args:
                value: Current progress value
                maximum: Maximum progress value
                message: Optional progress message
            """
            pass
        
        @abstractmethod
        def update_status(self, message: str) -> None:
            """
            Update status message.
            
            Args:
                message: Status message
            """
            pass
    ```

- [ ] **Implement PySide6 UI Service**
  - [ ] Create `src/app/services/pyside_ui_service.py` with the following content:
    ```python
    # src/app/services/pyside_ui_service.py
    from typing import Dict, Any, Optional, List, Union, Callable
    from pathlib import Path
    import os
    from PySide6.QtWidgets import (
        QMessageBox, QFileDialog, QApplication, QProgressDialog
    )
    from PySide6.QtCore import Qt, Signal, QObject
    from .ui_service import UIService

    class SignalEmitter(QObject):
        """Signal emitter for PySide6 UI Service."""
        status_updated = Signal(str)
        progress_updated = Signal(int, int, str)

    class PySideUIService(UIService):
        """UI service implementation using PySide6."""
        
        def __init__(self, parent=None, debug: bool = False):
            """
            Initialize the UI service.
            
            Args:
                parent: Parent widget
                debug: Whether to enable debug output
            """
            self.debug = debug
            self.parent = parent
            self.signals = SignalEmitter()
            self.progress_dialog = None
            
        def show_message(
            self,
            title: str,
            message: str,
            message_type: str = "info"
        ) -> None:
            """Show a message dialog."""
            try:
                # Map message type to QMessageBox icon
                icon_map = {
                    "info": QMessageBox.Information,
                    "warning": QMessageBox.Warning,
                    "error": QMessageBox.Critical,
                    "question": QMessageBox.Question
                }
                
                icon = icon_map.get(message_type.lower(), QMessageBox.Information)
                
                # Create and show message box
                msg_box = QMessageBox(self.parent)
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.setIcon(icon)
                msg_box.setStandardButtons(QMessageBox.Ok)
                
                # Show the dialog
                msg_box.exec()
                
            except Exception as e:
                if self.debug:
                    print(f"Error showing message: {str(e)}")
                
        def show_file_dialog(
            self,
            dialog_type: str = "open",
            title: str = "Select File",
            directory: Optional[Union[str, Path]] = None,
            file_filter: str = "All Files (*.*)"
        ) -> Optional[str]:
            """Show a file dialog."""
            try:
                # Get starting directory
                if directory:
                    if isinstance(directory, Path):
                        directory = str(directory)
                else:
                    directory = os.path.expanduser("~")
                    
                # Create dialog based on type
                if dialog_type.lower() == "save":
                    file_path, _ = QFileDialog.getSaveFileName(
                        self.parent,
                        title,
                        directory,
                        file_filter
                    )
                else:
                    file_path, _ = QFileDialog.getOpenFileName(
                        self.parent,
                        title,
                        directory,
                        file_filter
                    )
                    
                return file_path if file_path else None
                
            except Exception as e:
                if self.debug:
                    print(f"Error showing file dialog: {str(e)}")
                return None
                
        def show_directory_dialog(
            self,
            title: str = "Select Directory",
            directory: Optional[Union[str, Path]] = None
        ) -> Optional[str]:
            """Show a directory selection dialog."""
            try:
                # Get starting directory
                if directory:
                    if isinstance(directory, Path):
                        directory = str(directory)
                else:
                    directory = os.path.expanduser("~")
                    
                # Show directory dialog
                dir_path = QFileDialog.getExistingDirectory(
                    self.parent,
                    title,
                    directory,
                    QFileDialog.ShowDirsOnly
                )
                
                return dir_path if dir_path else None
                
            except Exception as e:
                if self.debug:
                    print(f"Error showing directory dialog: {str(e)}")
                return None
                
        def show_progress(
            self,
            value: int,
            maximum: int,
            message: Optional[str] = None
        ) -> None:
            """Update progress indicator."""
            try:
                # Emit signal for progress update
                self.signals.progress_updated.emit(value, maximum, message or "")
                
                # Create progress dialog if running in direct mode
                if self.parent and not self.progress_dialog:
                    self.progress_dialog = QProgressDialog(
                        message or "Processing...",
                        "Cancel",
                        0,
                        maximum,
                        self.parent
                    )
                    self.progress_dialog.setWindowModality(Qt.WindowModal)
                    self.progress_dialog.setAutoClose(True)
                    self.progress_dialog.setAutoReset(True)
                    
                # Update existing dialog
                if self.progress_dialog:
                    if message:
                        self.progress_dialog.setLabelText(message)
                    
                    self.progress_dialog.setValue(value)
                    
                    # Close if complete
                    if value >= maximum:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                        
            except Exception as e:
                if self.debug:
                    print(f"Error showing progress: {str(e)}")
                
        def update_status(self, message: str) -> None:
            """Update status message."""
            try:
                # Emit signal for status update
                self.signals.status_updated.emit(message)
                
            except Exception as e:
                if self.debug:
                    print(f"Error updating status: {str(e)}")
    ```

### 4. File Service

- [ ] **Create File Service Interface**
  - [ ] Create `src/app/services/file_service.py` with the following content:
    ```python
    # src/app/services/file_service.py
    from abc import ABC, abstractmethod
    from typing import Dict, Any, Optional, List, Union, BinaryIO
    from pathlib import Path
    import os

    class FileService(ABC):
        """Interface for file operations."""
        
        @abstractmethod
        def read_text_file(
            self,
            file_path: Union[str, Path],
            encoding: str = "utf-8"
        ) -> Optional[str]:
            """
            Read a text file.
            
            Args:
                file_path: Path to the file
                encoding: File encoding
                
            Returns:
                File contents as string, or None if error
            """
            pass
        
        @abstractmethod
        def write_text_file(
            self,
            file_path: Union[str, Path],
            content: str,
            encoding: str = "utf-8"
        ) -> bool:
            """
            Write a text file.
            
            Args:
                file_path: Path to the file
                content: Content to write
                encoding: File encoding
                
            Returns:
                True if successful, False otherwise
            """
            pass
        
        @abstractmethod
        def read_binary_file(
            self,
            file_path: Union[str, Path]
        ) -> Optional[bytes]:
            """
            Read a binary file.
            
            Args:
                file_path: Path to the file
                
            Returns:
                File contents as bytes, or None if error
            """
            pass
        
        @abstractmethod
        def write_binary_file(
            self,
            file_path: Union[str, Path],
            content: bytes
        ) -> bool:
            """
            Write a binary file.
            
            Args:
                file_path: Path to the file
                content: Content to write
                
            Returns:
                True if successful, False otherwise
            """
            pass
        
        @abstractmethod
        def file_exists(self, file_path: Union[str, Path]) -> bool:
            """
            Check if a file exists.
            
            Args:
                file_path: Path to check
                
            Returns:
                True if file exists, False otherwise
            """
            pass
        
        @abstractmethod
        def ensure_directory(self, directory_path: Union[str, Path]) -> bool:
            """
            Ensure a directory exists, creating it if necessary.
            
            Args:
                directory_path: Path to ensure exists
                
            Returns:
                True if successful, False otherwise
            """
            pass
    ```

- [ ] **Implement Native File Service**
  - [ ] Create `src/app/services/native_file_service.py` with implementation details
  
### 5. Application Service Registry

- [ ] **Create Service Registry**
  - [ ] Create `src/app/services/service_registry.py` with the following content:
    ```python
    # src/app/services/service_registry.py
    from typing import Dict, Any, Optional, Type, TypeVar, Generic, cast
    import inspect

    T = TypeVar('T')

    class ServiceRegistry:
        """Registry for application services."""
        
        _instance = None
        
        def __new__(cls):
            """Implement singleton pattern."""
            if cls._instance is None:
                cls._instance = super(ServiceRegistry, cls).__new__(cls)
                cls._instance._services = {}
                cls._instance._interfaces = {}
            return cls._instance
        
        def register(self, interface_type: Type, service_instance: Any) -> None:
            """
            Register a service implementation.
            
            Args:
                interface_type: Interface type
                service_instance: Service implementation instance
            """
            # Verify the service implements the interface
            if not isinstance(service_instance, interface_type):
                class_name = service_instance.__class__.__name__
                interface_name = interface_type.__name__
                raise TypeError(f"{class_name} does not implement {interface_name}")
                
            # Register the service
            self._services[interface_type] = service_instance
            
            # Register all interfaces this service implements
            for base in inspect.getmro(service_instance.__class__):
                if base is not object and inspect.isabstract(base):
                    self._interfaces[base] = interface_type
        
        def get(self, interface_type: Type[T]) -> Optional[T]:
            """
            Get a service implementation.
            
            Args:
                interface_type: Interface type
                
            Returns:
                Service implementation or None if not registered
            """
            # Direct lookup
            if interface_type in self._services:
                return cast(T, self._services[interface_type])
                
            # Check if registered as a different interface
            if interface_type in self._interfaces:
                return cast(T, self._services[self._interfaces[interface_type]])
                
            return None
            
        def has(self, interface_type: Type) -> bool:
            """
            Check if a service is registered.
            
            Args:
                interface_type: Interface type
                
            Returns:
                True if service is registered, False otherwise
            """
            return (interface_type in self._services or 
                   interface_type in self._interfaces)
                   
        def remove(self, interface_type: Type) -> bool:
            """
            Remove a service registration.
            
            Args:
                interface_type: Interface type
                
            Returns:
                True if service was removed, False otherwise
            """
            if interface_type in self._services:
                del self._services[interface_type]
                
                # Remove from interfaces mapping
                interfaces_to_remove = []
                for interface, impl_type in self._interfaces.items():
                    if impl_type == interface_type:
                        interfaces_to_remove.append(interface)
                        
                for interface in interfaces_to_remove:
                    del self._interfaces[interface]
                    
                return True
            
            return False
            
        def clear(self) -> None:
            """Clear all service registrations."""
            self._services.clear()
            self._interfaces.clear()
    ```

### 6. Application Service Integration

- [ ] **Create Service Provider**
  - [ ] Create `src/app/services/service_provider.py` with the following content:
    ```python
    # src/app/services/service_provider.py
    from typing import Dict, Any, Optional, Type, TypeVar, Generic, cast
    from pathlib import Path
    import os
    from .service_registry import ServiceRegistry
    from .config_service import ConfigService
    from .file_config_service import FileConfigService
    from .ui_service import UIService
    from .pyside_ui_service import PySideUIService
    from .file_service import FileService
    from .native_file_service import NativeFileService

    class ServiceProvider:
        """Provider for application services."""
        
        def __init__(self, app_directory: Optional[Path] = None):
            """
            Initialize the service provider.
            
            Args:
                app_directory: Application directory
            """
            self.registry = ServiceRegistry()
            self.app_directory = app_directory or Path.cwd()
            
            # Initialize services
            self._initialize_services()
            
        def _initialize_services(self) -> None:
            """Initialize all application services."""
            # Create config service
            config_file = self.app_directory / "config" / "app_config.ini"
            config_service = FileConfigService(config_file)
            self.registry.register(ConfigService, config_service)
            
            # Create UI service
            ui_service = PySideUIService()
            self.registry.register(UIService, ui_service)
            
            # Create file service
            file_service = NativeFileService()
            self.registry.register(FileService, file_service)
            
            # Register additional services as needed
            # ...
            
        def get_service(self, service_type: Type[Any]) -> Any:
            """
            Get a service by type.
            
            Args:
                service_type: Service interface type
                
            Returns:
                Service instance or None if not found
            """
            return self.registry.get(service_type)
    ```

- [ ] **Create Service Initialization**
  - [ ] Update `src/app/application.py` to use the service provider

### 7. Documentation

- [ ] **Update Application Service Documentation**
  - [ ] Add detailed docstrings to all classes and methods
  - [ ] Create examples for common service usage patterns
  - [ ] Document error handling and debugging procedures

- [ ] **Create Application Service Guide**
  - [ ] Create a guide for using the application services
  - [ ] Include examples of common service usage scenarios
  - [ ] Add troubleshooting section for common issues

### 8. Part 4 Validation

- [ ] **Review Implementation**
  - [ ] Verify all required services are implemented
  - [ ] Check for proper error handling and robustness
  - [ ] Ensure code quality meets project standards

- [ ] **Test Coverage Verification**
  - [ ] Verify test coverage of all services
  - [ ] Add tests for any missing functionality
  - [ ] Ensure edge cases are handled correctly

- [ ] **Documentation Verification**
  - [ ] Verify all services are properly documented
  - [ ] Update any outdated documentation
  - [ ] Ensure examples are clear and helpful

### Feedback Request

After completing Part 4 of Phase 3, please provide feedback on the following aspects:

1. Are the application services comprehensive enough for your needs?
2. Are there any additional services that should be included?
3. Is the service registration and provider approach appropriate?
4. Does the implementation align with the overall refactoring goals?
5. Any suggestions for improvements before proceeding to Part 5? 
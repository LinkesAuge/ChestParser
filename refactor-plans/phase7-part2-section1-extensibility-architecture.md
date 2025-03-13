# Phase 7 Part 2 - Section 1: Extensibility Architecture

## Overview
This document details the extensibility architecture for the Total Battle Analyzer application, which will serve as the foundation for the plugin and extension system. The architecture defines key extension points, interfaces, and the discovery mechanism that allows the application to be extended with custom functionality.

## Key Components

### 1. Extension Points
- Data processing extensions
- Analysis algorithm extensions
- Visualization extensions
- Report generation extensions
- UI component extensions

### 2. Plugin Interface Definitions
- Core plugin interface
- Plugin metadata structure
- Extension type-specific interfaces
- Plugin communication interfaces

### 3. Plugin Discovery Mechanism
- Plugin directory structure
- Manifest file format
- Dynamic loading system
- Plugin validation process

### 4. Extension Registry System
- Plugin registration
- Extension point mapping
- Dependency management
- Plugin lifecycle hooks

## Implementation Details

### 1.1 Core Extension System

```python
# src/goob_ai/plugin/core.py
from typing import Dict, List, Any, Optional, Type, Set, Callable
import importlib
import inspect
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod

class PluginInterface(ABC):
    """Base interface that all plugins must implement."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass
        
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Clean up resources when the plugin is being unloaded.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        pass
        
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata.
        
        Returns:
            Dict[str, Any]: Plugin metadata
        """
        pass

class PluginMetadata:
    """Represents plugin metadata."""
    
    def __init__(self, manifest_path: Path) -> None:
        """
        Initialize plugin metadata from a manifest file.
        
        Args:
            manifest_path: Path to the plugin manifest file
        """
        self.manifest_path = manifest_path
        self._metadata: Dict[str, Any] = self._load_manifest(manifest_path)
        
    def _load_manifest(self, manifest_path: Path) -> Dict[str, Any]:
        """
        Load plugin manifest data.
        
        Args:
            manifest_path: Path to the manifest file
            
        Returns:
            Dict[str, Any]: Manifest data
            
        Raises:
            ValueError: If manifest is invalid
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
                
            # Validate required fields
            required_fields = ['id', 'name', 'version', 'entry_point', 'min_app_version']
            for field in required_fields:
                if field not in manifest_data:
                    raise ValueError(f"Plugin manifest missing required field: {field}")
                    
            return manifest_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid plugin manifest format: {str(e)}")
            
    @property
    def id(self) -> str:
        """Get plugin ID."""
        return self._metadata['id']
        
    @property
    def name(self) -> str:
        """Get plugin name."""
        return self._metadata['name']
        
    @property
    def version(self) -> str:
        """Get plugin version."""
        return self._metadata['version']
        
    @property
    def description(self) -> str:
        """Get plugin description."""
        return self._metadata.get('description', '')
        
    @property
    def author(self) -> str:
        """Get plugin author."""
        return self._metadata.get('author', '')
        
    @property
    def entry_point(self) -> str:
        """Get plugin entry point."""
        return self._metadata['entry_point']
        
    @property
    def min_app_version(self) -> str:
        """Get minimum compatible application version."""
        return self._metadata['min_app_version']
        
    @property
    def dependencies(self) -> List[str]:
        """Get plugin dependencies."""
        return self._metadata.get('dependencies', [])
        
    @property
    def extension_points(self) -> List[str]:
        """Get extension points implemented by the plugin."""
        return self._metadata.get('extension_points', [])
        
    @property
    def permissions(self) -> List[str]:
        """Get permissions requested by the plugin."""
        return self._metadata.get('permissions', [])
        
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary."""
        return self._metadata.copy()
```

### 1.2 Extension Points Definition

```python
# src/goob_ai/plugin/extension_points.py
from typing import Dict, List, Any, Optional, Type, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
import pandas as pd

class ExtensionPointType(Enum):
    """Types of extension points available in the application."""
    
    DATA_PROCESSOR = auto()  # For data processing extensions
    ANALYSIS = auto()  # For analysis algorithm extensions
    VISUALIZATION = auto()  # For visualization extensions
    REPORT = auto()  # For report generation extensions
    UI_COMPONENT = auto()  # For UI component extensions

@runtime_checkable
class DataProcessorExtension(Protocol):
    """Protocol for data processor extensions."""
    
    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process a DataFrame.
        
        Args:
            data: Input DataFrame
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        ...
        
    def get_processor_info(self) -> Dict[str, Any]:
        """
        Get information about the processor.
        
        Returns:
            Dict[str, Any]: Processor metadata
        """
        ...

@runtime_checkable
class AnalysisExtension(Protocol):
    """Protocol for analysis algorithm extensions."""
    
    def analyze(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Analyze data and return results.
        
        Args:
            data: Input DataFrame
            **kwargs: Additional parameters for the analysis
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        ...
        
    def get_analysis_info(self) -> Dict[str, Any]:
        """
        Get information about the analysis.
        
        Returns:
            Dict[str, Any]: Analysis metadata
        """
        ...

@runtime_checkable
class VisualizationExtension(Protocol):
    """Protocol for visualization extensions."""
    
    def create_visualization(self, data: Dict[str, Any], **kwargs) -> Any:
        """
        Create a visualization from data.
        
        Args:
            data: Input data for visualization
            **kwargs: Additional parameters for visualization
            
        Returns:
            Any: Visualization object
        """
        ...
        
    def get_visualization_info(self) -> Dict[str, Any]:
        """
        Get information about the visualization.
        
        Returns:
            Dict[str, Any]: Visualization metadata
        """
        ...

class ReportExtension(ABC):
    """Abstract base class for report generation extensions."""
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        """
        Generate a report and save it to the specified path.
        
        Args:
            data: Input data for the report
            output_path: Path where the report should be saved
            **kwargs: Additional parameters for report generation
            
        Returns:
            Path: Path to the generated report
        """
        pass
        
    @abstractmethod
    def get_report_info(self) -> Dict[str, Any]:
        """
        Get information about the report generator.
        
        Returns:
            Dict[str, Any]: Report generator metadata
        """
        pass

class UIComponentExtension(ABC):
    """Abstract base class for UI component extensions."""
    
    @abstractmethod
    def create_component(self, parent: Any, **kwargs) -> Any:
        """
        Create a UI component.
        
        Args:
            parent: Parent UI element
            **kwargs: Additional parameters for component creation
            
        Returns:
            Any: Created UI component
        """
        pass
        
    @abstractmethod
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get information about the UI component.
        
        Returns:
            Dict[str, Any]: Component metadata
        """
        pass

# Dictionary mapping extension point types to their interface/protocol
EXTENSION_POINT_INTERFACES = {
    ExtensionPointType.DATA_PROCESSOR: DataProcessorExtension,
    ExtensionPointType.ANALYSIS: AnalysisExtension,
    ExtensionPointType.VISUALIZATION: VisualizationExtension,
    ExtensionPointType.REPORT: ReportExtension,
    ExtensionPointType.UI_COMPONENT: UIComponentExtension
}
```

### 1.3 Plugin Discovery System

```python
# src/goob_ai/plugin/discovery.py
from typing import Dict, List, Any, Optional, Type, Set, Tuple
import importlib.util
import sys
import logging
from pathlib import Path
from .core import PluginInterface, PluginMetadata
from .extension_points import ExtensionPointType, EXTENSION_POINT_INTERFACES

logger = logging.getLogger(__name__)

class PluginDiscovery:
    """Discovers and loads plugins from the filesystem."""
    
    def __init__(self, plugins_directory: Path) -> None:
        """
        Initialize plugin discovery with plugins directory.
        
        Args:
            plugins_directory: Directory containing plugins
        """
        self.plugins_directory = plugins_directory
        self.plugins_directory.mkdir(parents=True, exist_ok=True)
        
    def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover available plugins.
        
        Returns:
            List[PluginMetadata]: List of discovered plugin metadata
        """
        discovered_plugins = []
        
        # Scan plugins directory
        for plugin_dir in self.plugins_directory.iterdir():
            if not plugin_dir.is_dir():
                continue
                
            # Look for manifest file
            manifest_path = plugin_dir / "manifest.json"
            if not manifest_path.exists():
                logger.warning(f"Plugin directory without manifest: {plugin_dir}")
                continue
                
            try:
                # Load plugin metadata
                metadata = PluginMetadata(manifest_path)
                discovered_plugins.append(metadata)
                logger.info(f"Discovered plugin: {metadata.id} (v{metadata.version})")
            except ValueError as e:
                logger.error(f"Error loading plugin manifest from {manifest_path}: {str(e)}")
                
        return discovered_plugins
        
    def load_plugin(self, metadata: PluginMetadata) -> Optional[PluginInterface]:
        """
        Load a plugin from its metadata.
        
        Args:
            metadata: Plugin metadata
            
        Returns:
            Optional[PluginInterface]: Loaded plugin instance or None if loading failed
        """
        try:
            # Determine plugin directory and entry point
            plugin_dir = self.plugins_directory / metadata.id
            entry_point = metadata.entry_point
            
            # Split entry point into module and class
            if ':' not in entry_point:
                logger.error(f"Invalid entry point format: {entry_point}")
                return None
                
            module_path, class_name = entry_point.split(':', 1)
            
            # Prepare absolute path to the module file
            if module_path.endswith('.py'):
                module_file = plugin_dir / module_path
            else:
                module_file = plugin_dir / f"{module_path}.py"
                
            if not module_file.exists():
                logger.error(f"Plugin module file not found: {module_file}")
                return None
                
            # Load module
            module_name = f"plugin_{metadata.id}_{module_path}"
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {module_file}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get plugin class
            if not hasattr(module, class_name):
                logger.error(f"Plugin class {class_name} not found in {module_file}")
                return None
                
            plugin_class = getattr(module, class_name)
            
            # Create plugin instance
            plugin = plugin_class()
            
            # Verify it implements PluginInterface
            if not isinstance(plugin, PluginInterface):
                logger.error(f"Plugin class {class_name} does not implement PluginInterface")
                return None
                
            return plugin
            
        except Exception as e:
            logger.error(f"Error loading plugin {metadata.id}: {str(e)}")
            return None
            
    def validate_plugin_extension_points(self, plugin: PluginInterface) -> Dict[ExtensionPointType, bool]:
        """
        Validate that a plugin correctly implements its declared extension points.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            Dict[ExtensionPointType, bool]: Dictionary mapping extension points to validation results
        """
        validation_results = {}
        metadata = plugin.metadata
        
        if 'extension_points' not in metadata:
            return {}
            
        for extension_point_str in metadata['extension_points']:
            try:
                # Convert string to enum
                extension_point = ExtensionPointType[extension_point_str]
                
                # Get the expected interface
                expected_interface = EXTENSION_POINT_INTERFACES[extension_point]
                
                # Check if plugin implements the interface
                implements_interface = isinstance(plugin, expected_interface)
                validation_results[extension_point] = implements_interface
                
                if not implements_interface:
                    logger.warning(f"Plugin {metadata['id']} declares extension point "
                                  f"{extension_point_str} but doesn't implement the required interface")
                    
            except (KeyError, ValueError):
                logger.error(f"Unknown extension point: {extension_point_str}")
                
        return validation_results
```

### 1.4 Extension Registry

```python
# src/goob_ai/plugin/registry.py
from typing import Dict, List, Any, Optional, Type, Set, Callable
import logging
from pathlib import Path
from .core import PluginInterface, PluginMetadata
from .discovery import PluginDiscovery
from .extension_points import ExtensionPointType

logger = logging.getLogger(__name__)

class PluginRegistry:
    """Central registry for plugins and extension points."""
    
    def __init__(self, plugins_directory: Path) -> None:
        """
        Initialize plugin registry.
        
        Args:
            plugins_directory: Directory containing plugins
        """
        self.plugins_directory = plugins_directory
        self.discovery = PluginDiscovery(plugins_directory)
        
        # Plugin storage
        self.available_plugins: Dict[str, PluginMetadata] = {}
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        
        # Extension point mappings
        self.extension_points: Dict[ExtensionPointType, List[str]] = {
            ext_type: [] for ext_type in ExtensionPointType
        }
        
        # Lifecycle callbacks
        self.on_plugin_loaded_callbacks: List[Callable[[str, PluginInterface], None]] = []
        self.on_plugin_unloaded_callbacks: List[Callable[[str], None]] = []
        
    def discover_available_plugins(self) -> List[PluginMetadata]:
        """
        Discover available plugins and update registry.
        
        Returns:
            List[PluginMetadata]: List of discovered plugin metadata
        """
        discovered = self.discovery.discover_plugins()
        
        # Update available plugins
        for metadata in discovered:
            self.available_plugins[metadata.id] = metadata
            
        return discovered
        
    def register_lifecycle_callback(self, 
                                  on_loaded: Optional[Callable[[str, PluginInterface], None]] = None,
                                  on_unloaded: Optional[Callable[[str], None]] = None) -> None:
        """
        Register callbacks for plugin lifecycle events.
        
        Args:
            on_loaded: Callback when a plugin is loaded
            on_unloaded: Callback when a plugin is unloaded
        """
        if on_loaded:
            self.on_plugin_loaded_callbacks.append(on_loaded)
            
        if on_unloaded:
            self.on_plugin_unloaded_callbacks.append(on_unloaded)
            
    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            bool: True if the plugin was loaded successfully, False otherwise
        """
        # Check if plugin is already loaded
        if plugin_id in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} is already loaded")
            return True
            
        # Check if plugin is available
        if plugin_id not in self.available_plugins:
            logger.error(f"Plugin {plugin_id} is not available")
            return False
            
        metadata = self.available_plugins[plugin_id]
        
        # Load plugin
        plugin = self.discovery.load_plugin(metadata)
        if plugin is None:
            logger.error(f"Failed to load plugin {plugin_id}")
            return False
            
        # Initialize plugin
        try:
            if not plugin.initialize():
                logger.error(f"Plugin {plugin_id} initialization failed")
                return False
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_id}: {str(e)}")
            return False
            
        # Validate extension points
        validation_results = self.discovery.validate_plugin_extension_points(plugin)
        
        # Register extension points
        for ext_type, is_valid in validation_results.items():
            if is_valid:
                self.extension_points[ext_type].append(plugin_id)
                
        # Store loaded plugin
        self.loaded_plugins[plugin_id] = plugin
        
        # Trigger callbacks
        for callback in self.on_plugin_loaded_callbacks:
            try:
                callback(plugin_id, plugin)
            except Exception as e:
                logger.error(f"Error in plugin loaded callback: {str(e)}")
                
        logger.info(f"Plugin {plugin_id} loaded successfully")
        return True
        
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            bool: True if the plugin was unloaded successfully, False otherwise
        """
        # Check if plugin is loaded
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} is not loaded")
            return False
            
        plugin = self.loaded_plugins[plugin_id]
        
        # Shutdown plugin
        try:
            if not plugin.shutdown():
                logger.error(f"Plugin {plugin_id} shutdown failed")
                return False
        except Exception as e:
            logger.error(f"Error shutting down plugin {plugin_id}: {str(e)}")
            return False
            
        # Remove from extension points
        for ext_list in self.extension_points.values():
            if plugin_id in ext_list:
                ext_list.remove(plugin_id)
                
        # Remove from loaded plugins
        del self.loaded_plugins[plugin_id]
        
        # Trigger callbacks
        for callback in self.on_plugin_unloaded_callbacks:
            try:
                callback(plugin_id)
            except Exception as e:
                logger.error(f"Error in plugin unloaded callback: {str(e)}")
                
        logger.info(f"Plugin {plugin_id} unloaded successfully")
        return True
        
    def get_extensions(self, extension_type: ExtensionPointType) -> List[PluginInterface]:
        """
        Get all loaded plugins implementing a specific extension point.
        
        Args:
            extension_type: Type of extension point
            
        Returns:
            List[PluginInterface]: List of plugin instances
        """
        if extension_type not in self.extension_points:
            return []
            
        plugin_ids = self.extension_points[extension_type]
        return [self.loaded_plugins[pid] for pid in plugin_ids if pid in self.loaded_plugins]
        
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """
        Get a loaded plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Optional[PluginInterface]: Plugin instance or None if not loaded
        """
        return self.loaded_plugins.get(plugin_id)
```

## Integration with Existing Application

### Plugin Management Service
1. Create a `PluginService` class that will:
   - Manage the plugin registry and discovery
   - Provide plugin-related functionality to the UI
   - Coordinate plugin lifecycle with the application

```python
# src/goob_ai/services/plugin_service.py
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import logging
from ..plugin.registry import PluginRegistry
from ..plugin.core import PluginInterface, PluginMetadata
from ..plugin.extension_points import ExtensionPointType

logger = logging.getLogger(__name__)

class PluginService:
    """Service for managing plugins."""
    
    def __init__(self, app_data_dir: Path) -> None:
        """
        Initialize the plugin service.
        
        Args:
            app_data_dir: Application data directory
        """
        self.plugins_dir = app_data_dir / "plugins"
        self.registry = PluginRegistry(self.plugins_dir)
        
        # Register lifecycle callbacks
        self.registry.register_lifecycle_callback(
            on_loaded=self._on_plugin_loaded,
            on_unloaded=self._on_plugin_unloaded
        )
        
    def _on_plugin_loaded(self, plugin_id: str, plugin: PluginInterface) -> None:
        """
        Handle plugin loaded event.
        
        Args:
            plugin_id: Plugin ID
            plugin: Plugin instance
        """
        logger.info(f"Plugin loaded: {plugin_id}")
        # Additional application-specific handling could be added here
        
    def _on_plugin_unloaded(self, plugin_id: str) -> None:
        """
        Handle plugin unloaded event.
        
        Args:
            plugin_id: Plugin ID
        """
        logger.info(f"Plugin unloaded: {plugin_id}")
        # Additional application-specific handling could be added here
        
    def initialize(self) -> None:
        """Initialize the plugin system."""
        # Discover available plugins
        available_plugins = self.registry.discover_available_plugins()
        logger.info(f"Discovered {len(available_plugins)} available plugins")
        
        # Auto-load enabled plugins
        # In the future, this could check a configuration file for enabled plugins
        
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of available plugins.
        
        Returns:
            List[Dict[str, Any]]: List of plugin metadata dictionaries
        """
        return [m.as_dict for m in self.registry.available_plugins.values()]
        
    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of loaded plugin IDs.
        
        Returns:
            List[str]: List of loaded plugin IDs
        """
        return list(self.registry.loaded_plugins.keys())
        
    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.registry.load_plugin(plugin_id)
        
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.registry.unload_plugin(plugin_id)
        
    def get_extensions_by_type(self, extension_type: ExtensionPointType) -> List[Dict[str, Any]]:
        """
        Get all extensions of a specific type.
        
        Args:
            extension_type: Extension point type
            
        Returns:
            List[Dict[str, Any]]: List of extension information
        """
        extensions = self.registry.get_extensions(extension_type)
        result = []
        
        for plugin in extensions:
            metadata = plugin.metadata
            
            # Get extension-specific info based on type
            if extension_type == ExtensionPointType.DATA_PROCESSOR:
                ext_info = plugin.get_processor_info()
            elif extension_type == ExtensionPointType.ANALYSIS:
                ext_info = plugin.get_analysis_info()
            elif extension_type == ExtensionPointType.VISUALIZATION:
                ext_info = plugin.get_visualization_info()
            elif extension_type == ExtensionPointType.REPORT:
                ext_info = plugin.get_report_info()
            elif extension_type == ExtensionPointType.UI_COMPONENT:
                ext_info = plugin.get_component_info()
            else:
                ext_info = {}
                
            result.append({
                'plugin_id': metadata['id'],
                'plugin_name': metadata['name'],
                'plugin_version': metadata['version'],
                'extension_info': ext_info
            })
            
        return result
```

## Example Plugin Structure

```
plugins/
  my_analysis_plugin/
    manifest.json
    plugin.py
    analysis_algorithm.py
    resources/
      README.md
      icon.png
```

Example manifest.json:
```json
{
    "id": "my_analysis_plugin",
    "name": "My Analysis Plugin",
    "version": "1.0.0",
    "description": "Adds a custom analysis algorithm",
    "author": "Jane Doe",
    "entry_point": "plugin:MyAnalysisPlugin",
    "min_app_version": "2.0.0",
    "extension_points": ["ANALYSIS"],
    "permissions": ["read_data"],
    "dependencies": []
}
```

Example plugin implementation:
```python
# plugin.py
from typing import Dict, Any
import pandas as pd
from goob_ai.plugin.core import PluginInterface
from goob_ai.plugin.extension_points import AnalysisExtension
from .analysis_algorithm import CustomAnalysisAlgorithm

class MyAnalysisPlugin(PluginInterface, AnalysisExtension):
    def __init__(self):
        self._metadata = {
            'id': 'my_analysis_plugin',
            'name': 'My Analysis Plugin',
            'version': '1.0.0',
            'description': 'Adds a custom analysis algorithm',
            'author': 'Jane Doe',
            'entry_point': 'plugin:MyAnalysisPlugin',
            'min_app_version': '2.0.0',
            'extension_points': ['ANALYSIS'],
            'permissions': ['read_data'],
            'dependencies': []
        }
        self.algorithm = CustomAnalysisAlgorithm()
    
    def initialize(self) -> bool:
        print("Initializing My Analysis Plugin")
        return True
    
    def shutdown(self) -> bool:
        print("Shutting down My Analysis Plugin")
        return True
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
    def analyze(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        return self.algorithm.run_analysis(data, **kwargs)
    
    def get_analysis_info(self) -> Dict[str, Any]:
        return {
            'name': 'Custom Analysis',
            'description': 'Performs custom analysis on battle data',
            'parameters': {
                'threshold': 'Threshold value for analysis (float)',
                'include_outliers': 'Whether to include outliers (bool)'
            }
        }
```

## Implementation Steps

### Week 1: Core Framework (Days 1-3)
1. Implement `PluginInterface` and `PluginMetadata` classes
2. Create extension point interfaces and protocols
3. Build basic plugin discovery mechanism
4. Develop initial extension registry

### Week 2: Integration & Testing (Days 4-7)
1. Implement `PluginService` for application integration
2. Create sample plugins for testing
3. Develop comprehensive tests for discovery and registry
4. Add error handling and logging

## Dependencies
- Python 3.8+
- typing-extensions (for Protocol support in Python < 3.8)
- jsonschema (for manifest validation)
- packaging (for version comparison)

## Testing Strategy
1. Unit tests for core plugin infrastructure
2. Tests with sample plugins of each extension type
3. Error handling tests (invalid manifests, failed initialization, etc.)

## Success Criteria
1. Extension point interfaces are clearly defined and usable
2. Plugin discovery correctly loads plugins from the filesystem
3. Registry properly tracks plugins and their extension points
4. Sample plugins can be loaded, initialized, and shutdown
5. Error handling is robust with clear messages 
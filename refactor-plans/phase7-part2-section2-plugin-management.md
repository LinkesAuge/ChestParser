# Phase 7 Part 2 - Section 2: Plugin Management System

## Overview
This document details the implementation of the plugin management system for the Total Battle Analyzer application. The plugin management system provides functionality for installing, configuring, enabling/disabling, and uninstalling plugins, along with a user-friendly interface for discovering and managing these plugins.

## Key Components

### 1. Plugin Lifecycle Management
- Plugin installation process
- Plugin activation/deactivation
- Plugin configuration storage
- Plugin updates and version management

### 2. Plugin Installation & Uninstallation
- Plugin package structure
- Installation validation
- Dependency resolution
- Clean uninstallation

### 3. Version Compatibility Verification
- Version comparison system
- Compatibility checking
- Upgrade/downgrade handling
- Dependency version resolution

### 4. Plugin Marketplace
- Plugin discovery interface
- Plugin catalog management
- Remote repository integration
- User ratings and reviews

## Implementation Details

### 2.1 Plugin Manager

```python
# src/goob_ai/plugin/manager.py
from typing import Dict, List, Any, Optional, Tuple
import os
import shutil
import zipfile
import json
import logging
import tempfile
from pathlib import Path
from packaging import version
from .registry import PluginRegistry
from .core import PluginMetadata, PluginInterface

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin lifecycle operations."""
    
    def __init__(self, registry: PluginRegistry, app_version: str) -> None:
        """
        Initialize the plugin manager.
        
        Args:
            registry: Plugin registry instance
            app_version: Current application version
        """
        self.registry = registry
        self.app_version = app_version
        self.plugins_dir = registry.plugins_directory
        self.enabled_plugins: List[str] = self._load_enabled_plugins()
        
    def _load_enabled_plugins(self) -> List[str]:
        """
        Load list of enabled plugins from config.
        
        Returns:
            List[str]: List of enabled plugin IDs
        """
        config_file = self.plugins_dir / "enabled_plugins.json"
        if not config_file.exists():
            return []
            
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading enabled plugins: {str(e)}")
            return []
            
    def _save_enabled_plugins(self) -> None:
        """Save list of enabled plugins to config."""
        config_file = self.plugins_dir / "enabled_plugins.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.enabled_plugins, f)
        except Exception as e:
            logger.error(f"Error saving enabled plugins: {str(e)}")
            
    def install_plugin(self, plugin_package_path: Path) -> Tuple[bool, str]:
        """
        Install a plugin from a package file.
        
        Args:
            plugin_package_path: Path to the plugin package file
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if not plugin_package_path.exists():
            return False, f"Plugin package not found: {plugin_package_path}"
            
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Extract plugin package
                if plugin_package_path.suffix == '.zip':
                    with zipfile.ZipFile(plugin_package_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                else:
                    return False, "Unsupported plugin package format"
                    
                # Check for manifest
                manifest_path = temp_path / "manifest.json"
                if not manifest_path.exists():
                    return False, "Invalid plugin package: manifest.json not found"
                    
                # Load metadata
                metadata = PluginMetadata(manifest_path)
                plugin_id = metadata.id
                
                # Check if plugin is already installed
                target_dir = self.plugins_dir / plugin_id
                if target_dir.exists():
                    return False, f"Plugin {plugin_id} is already installed"
                    
                # Check version compatibility
                if not self._is_compatible(metadata):
                    return False, (f"Plugin {plugin_id} requires minimum app version "
                                  f"{metadata.min_app_version}, but current version is {self.app_version}")
                    
                # Check dependencies
                missing_deps = self._check_dependencies(metadata)
                if missing_deps:
                    return False, f"Missing dependencies: {', '.join(missing_deps)}"
                    
                # Copy plugin files to plugins directory
                target_dir.mkdir(parents=True, exist_ok=True)
                
                for item in temp_path.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, target_dir / item.name)
                        
                # Re-discover plugins to include the new one
                self.registry.discover_available_plugins()
                
                return True, f"Plugin {plugin_id} installed successfully"
                
            except Exception as e:
                logger.error(f"Error installing plugin: {str(e)}")
                return False, f"Error installing plugin: {str(e)}"
                
    def uninstall_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Uninstall a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        # Check if plugin exists
        plugin_dir = self.plugins_dir / plugin_id
        if not plugin_dir.exists():
            return False, f"Plugin {plugin_id} is not installed"
            
        # Check if plugin is loaded
        if plugin_id in self.registry.loaded_plugins:
            # Try to unload plugin
            if not self.registry.unload_plugin(plugin_id):
                return False, f"Failed to unload plugin {plugin_id} before uninstallation"
                
        # Remove from enabled plugins
        if plugin_id in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_id)
            self._save_enabled_plugins()
            
        try:
            # Remove plugin directory
            shutil.rmtree(plugin_dir)
            
            # Remove from available plugins
            if plugin_id in self.registry.available_plugins:
                del self.registry.available_plugins[plugin_id]
                
            return True, f"Plugin {plugin_id} uninstalled successfully"
            
        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_id}: {str(e)}")
            return False, f"Error uninstalling plugin: {str(e)}"
            
    def enable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Enable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        # Check if plugin exists
        if plugin_id not in self.registry.available_plugins:
            return False, f"Plugin {plugin_id} is not installed"
            
        # Check if already enabled
        if plugin_id in self.enabled_plugins:
            return True, f"Plugin {plugin_id} is already enabled"
            
        # Check compatibility
        metadata = self.registry.available_plugins[plugin_id]
        if not self._is_compatible(metadata):
            return False, (f"Plugin {plugin_id} requires minimum app version "
                          f"{metadata.min_app_version}, but current version is {self.app_version}")
            
        # Check dependencies
        missing_deps = self._check_dependencies(metadata)
        if missing_deps:
            return False, f"Missing dependencies: {', '.join(missing_deps)}"
            
        # Add to enabled plugins
        self.enabled_plugins.append(plugin_id)
        self._save_enabled_plugins()
        
        return True, f"Plugin {plugin_id} enabled successfully"
        
    def disable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Disable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        # Check if plugin is enabled
        if plugin_id not in self.enabled_plugins:
            return False, f"Plugin {plugin_id} is not enabled"
            
        # Check if plugin is loaded
        if plugin_id in self.registry.loaded_plugins:
            # Try to unload plugin
            if not self.registry.unload_plugin(plugin_id):
                return False, f"Failed to unload plugin {plugin_id}"
                
        # Remove from enabled plugins
        self.enabled_plugins.remove(plugin_id)
        self._save_enabled_plugins()
        
        return True, f"Plugin {plugin_id} disabled successfully"
        
    def load_enabled_plugins(self) -> Dict[str, bool]:
        """
        Load all enabled plugins.
        
        Returns:
            Dict[str, bool]: Dictionary mapping plugin IDs to load success status
        """
        results = {}
        
        for plugin_id in self.enabled_plugins:
            if plugin_id in self.registry.loaded_plugins:
                results[plugin_id] = True
                continue
                
            success = self.registry.load_plugin(plugin_id)
            results[plugin_id] = success
            
            if not success:
                logger.error(f"Failed to load enabled plugin {plugin_id}")
                
        return results
        
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Dict[str, Any]: Plugin configuration
        """
        config_file = self.plugins_dir / plugin_id / "config.json"
        
        if not config_file.exists():
            return {}
            
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading plugin config: {str(e)}")
            return {}
            
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """
        Save plugin configuration.
        
        Args:
            plugin_id: Plugin ID
            config: Configuration to save
            
        Returns:
            bool: Success status
        """
        plugin_dir = self.plugins_dir / plugin_id
        
        if not plugin_dir.exists():
            return False
            
        config_file = plugin_dir / "config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving plugin config: {str(e)}")
            return False
            
    def _is_compatible(self, metadata: PluginMetadata) -> bool:
        """
        Check if a plugin is compatible with the current app version.
        
        Args:
            metadata: Plugin metadata
            
        Returns:
            bool: True if compatible, False otherwise
        """
        min_version = metadata.min_app_version
        current_version = self.app_version
        
        try:
            return version.parse(current_version) >= version.parse(min_version)
        except Exception:
            logger.error(f"Error comparing versions: {min_version} vs {current_version}")
            return False
            
    def _check_dependencies(self, metadata: PluginMetadata) -> List[str]:
        """
        Check if all dependencies are available.
        
        Args:
            metadata: Plugin metadata
            
        Returns:
            List[str]: List of missing dependencies
        """
        missing = []
        
        for dep_id in metadata.dependencies:
            if dep_id not in self.registry.available_plugins:
                missing.append(dep_id)
                
        return missing
```

### 2.2 Plugin Marketplace Interface

```python
# src/goob_ai/plugin/marketplace.py
from typing import Dict, List, Any, Optional, Tuple
import os
import json
import logging
import requests
import tempfile
from pathlib import Path
from .manager import PluginManager

logger = logging.getLogger(__name__)

class PluginMarketplace:
    """Interface for discovering and installing plugins from repositories."""
    
    def __init__(self, plugin_manager: PluginManager, config_dir: Path) -> None:
        """
        Initialize the plugin marketplace.
        
        Args:
            plugin_manager: Plugin manager instance
            config_dir: Configuration directory
        """
        self.plugin_manager = plugin_manager
        self.config_dir = config_dir
        self.config_file = config_dir / "marketplace.json"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load marketplace configuration.
        
        Returns:
            Dict[str, Any]: Marketplace configuration
        """
        if not self.config_file.exists():
            # Default configuration
            default_config = {
                "repositories": [
                    {
                        "name": "Official Repository",
                        "url": "https://plugins.totalbattleanalyzer.com/api/v1",
                        "enabled": True
                    }
                ]
            }
            
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config
            
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading marketplace config: {str(e)}")
            return {"repositories": []}
            
    def _save_config(self) -> None:
        """Save marketplace configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving marketplace config: {str(e)}")
            
    def get_repositories(self) -> List[Dict[str, Any]]:
        """
        Get list of configured repositories.
        
        Returns:
            List[Dict[str, Any]]: List of repository configurations
        """
        return self.config.get("repositories", [])
        
    def add_repository(self, name: str, url: str) -> bool:
        """
        Add a new repository.
        
        Args:
            name: Repository name
            url: Repository URL
            
        Returns:
            bool: Success status
        """
        repositories = self.get_repositories()
        
        # Check if repository already exists
        for repo in repositories:
            if repo["url"] == url:
                return False
                
        # Add new repository
        repositories.append({
            "name": name,
            "url": url,
            "enabled": True
        })
        
        self.config["repositories"] = repositories
        self._save_config()
        
        return True
        
    def remove_repository(self, url: str) -> bool:
        """
        Remove a repository.
        
        Args:
            url: Repository URL
            
        Returns:
            bool: Success status
        """
        repositories = self.get_repositories()
        
        # Filter out the repository to remove
        new_repositories = [repo for repo in repositories if repo["url"] != url]
        
        if len(new_repositories) == len(repositories):
            return False
            
        self.config["repositories"] = new_repositories
        self._save_config()
        
        return True
        
    def get_available_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of available plugins from all enabled repositories.
        
        Returns:
            List[Dict[str, Any]]: List of available plugin metadata
        """
        all_plugins = []
        
        for repo in self.get_repositories():
            if not repo.get("enabled", True):
                continue
                
            try:
                url = repo["url"] + "/plugins"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                plugins = response.json()
                
                # Add repository information to each plugin
                for plugin in plugins:
                    plugin["repository"] = {
                        "name": repo["name"],
                        "url": repo["url"]
                    }
                    
                all_plugins.extend(plugins)
                
            except Exception as e:
                logger.error(f"Error fetching plugins from repository {repo['name']}: {str(e)}")
                
        return all_plugins
        
    def install_plugin_from_repository(self, plugin_id: str, repo_url: str) -> Tuple[bool, str]:
        """
        Install a plugin from a repository.
        
        Args:
            plugin_id: Plugin ID
            repo_url: Repository URL
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        try:
            # Download plugin package
            url = f"{repo_url}/plugins/{plugin_id}/download"
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
                # Write content to temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                    
            # Install plugin from temporary file
            success, message = self.plugin_manager.install_plugin(temp_path)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error installing plugin from repository: {str(e)}")
            return False, f"Error installing plugin: {str(e)}"
            
    def get_plugin_details(self, plugin_id: str, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a plugin.
        
        Args:
            plugin_id: Plugin ID
            repo_url: Repository URL
            
        Returns:
            Optional[Dict[str, Any]]: Plugin details or None if not found
        """
        try:
            url = f"{repo_url}/plugins/{plugin_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching plugin details: {str(e)}")
            return None
```

## Integration with User Interface

### Plugin Manager UI
The plugin manager will integrate with the UI through a dedicated plugin management screen that allows users to:
1. View installed plugins
2. Browse available plugins in the marketplace
3. Install, uninstall, enable, and disable plugins
4. Configure plugin settings

```python
# src/goob_ai/controllers/plugin_controller.py
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from ..services.plugin_service import PluginService
from ..plugin.extension_points import ExtensionPointType

class PluginController:
    """Controller for plugin management UI."""
    
    def __init__(self, plugin_service: PluginService) -> None:
        """
        Initialize plugin controller.
        
        Args:
            plugin_service: Plugin service instance
        """
        self.plugin_service = plugin_service
        
    def get_installed_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of installed plugins.
        
        Returns:
            List[Dict[str, Any]]: List of plugin metadata
        """
        plugins = self.plugin_service.get_available_plugins()
        loaded_plugins = self.plugin_service.get_loaded_plugins()
        enabled_plugins = self.plugin_service.get_enabled_plugins()
        
        # Add loaded and enabled status to each plugin
        for plugin in plugins:
            plugin_id = plugin['id']
            plugin['is_loaded'] = plugin_id in loaded_plugins
            plugin['is_enabled'] = plugin_id in enabled_plugins
            
        return plugins
        
    def get_marketplace_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of available plugins from marketplace.
        
        Returns:
            List[Dict[str, Any]]: List of plugin metadata
        """
        return self.plugin_service.get_marketplace_plugins()
        
    def install_plugin(self, plugin_id: str, repo_url: Optional[str] = None) -> Tuple[bool, str]:
        """
        Install a plugin.
        
        Args:
            plugin_id: Plugin ID
            repo_url: Repository URL (optional, for marketplace plugins)
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        if repo_url:
            return self.plugin_service.install_plugin_from_repository(plugin_id, repo_url)
        else:
            return self.plugin_service.install_plugin_from_file(plugin_id)
            
    def uninstall_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Uninstall a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        return self.plugin_service.uninstall_plugin(plugin_id)
        
    def enable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Enable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        return self.plugin_service.enable_plugin(plugin_id)
        
    def disable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Disable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple[bool, str]: (Success, Message)
        """
        return self.plugin_service.disable_plugin(plugin_id)
        
    def get_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Dict[str, Any]: Plugin configuration
        """
        return self.plugin_service.get_plugin_config(plugin_id)
        
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """
        Save plugin configuration.
        
        Args:
            plugin_id: Plugin ID
            config: Configuration to save
            
        Returns:
            bool: Success status
        """
        return self.plugin_service.save_plugin_config(plugin_id, config)
```

## Implementation Steps

### Week 1: Core Management Functionality (Days 1-4)
1. Implement `PluginManager` class for lifecycle management
2. Create installation and uninstallation functionality
3. Build enable/disable capability
4. Add configuration storage and retrieval

### Week 2: Marketplace & UI Integration (Days 5-7)
1. Implement `PluginMarketplace` class
2. Create repository management functionality
3. Build plugin discovery and installation from repositories
4. Integrate with UI controller

## Dependencies
- Python 3.8+
- requests (for marketplace functionality)
- packaging (for version comparison)
- zipfile (built-in, for package handling)

## Testing Strategy
1. Unit tests for plugin management functions
2. Integration tests with sample plugins
3. Error handling tests (invalid packages, installation failures, etc.)
4. Marketplace integration tests (may require mock server)

## Success Criteria
1. Plugins can be installed, uninstalled, enabled, and disabled
2. Plugin configuration is properly saved and loaded
3. Version compatibility checks work correctly
4. Marketplace integration provides access to remote plugins
5. UI integration provides intuitive plugin management experience 
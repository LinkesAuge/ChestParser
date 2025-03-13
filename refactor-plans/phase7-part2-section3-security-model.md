# Phase 7 Part 2 - Section 3: Security Model for Third-Party Code

## Overview
This document details the security model for third-party plugins in the Total Battle Analyzer application. The security model ensures that plugins can extend the application's functionality without compromising system security, user data, or application stability. It implements a sandbox environment with controlled access to resources and permission-based capabilities.

## Key Components

### 1. Plugin Sandboxing
- Execution isolation
- Resource constraints
- Memory management
- CPU usage limitations

### 2. Permission System
- Capability-based security model
- Permission declaration in manifest
- User approval for sensitive permissions
- Permission enforcement during execution

### 3. Code Validation
- Static code analysis
- Dependency validation
- Known vulnerability scanning
- Malicious pattern detection

### 4. Runtime Monitoring
- Plugin behavior monitoring
- Resource usage tracking
- Security violation detection
- Plugin isolation on violation

## Implementation Details

### 3.1 Plugin Sandbox Environment

```python
# src/goob_ai/plugin/sandbox.py
from typing import Dict, List, Any, Optional, Callable, Set
import inspect
import sys
import logging
import threading
import time
import resource
from pathlib import Path
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins, limited_builtins, guarded_getattr
from RestrictedPython.PrintCollector import PrintCollector

logger = logging.getLogger(__name__)

class PluginSandbox:
    """Sandbox environment for safely executing plugin code."""
    
    # Set of allowed built-in modules for plugins
    ALLOWED_MODULES = {
        'math', 'datetime', 'time', 'json', 're', 
        'collections', 'itertools', 'functools',
        'typing', 'enum', 'uuid', 'pathlib'
    }
    
    # Set of dangerous attributes that should never be allowed
    FORBIDDEN_ATTRIBUTES = {
        '__subclasses__', '__bases__', '__class__', '__mro__',
        '__getattribute__', '__setattr__', '__delattr__',
        'eval', 'exec', 'compile', '__import__'
    }
    
    def __init__(self, max_memory_mb: int = 100, max_cpu_time: int = 10) -> None:
        """
        Initialize the plugin sandbox environment.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            max_cpu_time: Maximum CPU time in seconds
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time
        self.global_scope: Dict[str, Any] = {}
        
        # Initialize safe globals
        self._init_safe_globals()
        
    def _init_safe_globals(self) -> None:
        """Initialize safe globals for restricted execution."""
        # Create a safe environment for plugins
        self.global_scope = {
            '__builtins__': safe_builtins,
            '_print_': PrintCollector,
            '_getattr_': self._guarded_getattr,
            '_getitem_': self._guarded_getitem,
            '_write_': self._guarded_write,
            'Path': self._restricted_path,
        }
        
        # Add allowed modules to the safe environment
        for module_name in self.ALLOWED_MODULES:
            try:
                self.global_scope[module_name] = __import__(module_name)
            except ImportError:
                pass
                
    def _guarded_getattr(self, obj: Any, name: str) -> Any:
        """
        Guarded attribute access for restricted code.
        
        Args:
            obj: Object to access
            name: Attribute name
            
        Returns:
            The attribute value if allowed, raises AttributeError otherwise
        """
        # Check for forbidden attributes
        if name in self.FORBIDDEN_ATTRIBUTES:
            raise AttributeError(f"Access to '{name}' is forbidden")
            
        # Check for dunder methods
        if name.startswith('__') and name.endswith('__'):
            # Allow some safe dunder methods
            safe_dunders = {'__str__', '__repr__', '__len__', '__iter__', '__next__'}
            if name not in safe_dunders:
                raise AttributeError(f"Access to '{name}' is forbidden")
        
        # Use RestrictedPython's guarded_getattr for additional safety
        return guarded_getattr(obj, name)
        
    def _guarded_getitem(self, obj: Any, key: Any) -> Any:
        """
        Guarded item access for restricted code.
        
        Args:
            obj: Object to access
            key: Key to use
            
        Returns:
            The item value
        """
        # Basic implementation - can be extended with additional checks
        return obj[key]
        
    def _guarded_write(self, obj: Any) -> str:
        """
        Guarded write operation for restricted code.
        
        Args:
            obj: Object to write
            
        Returns:
            String representation
        """
        # Only allow string outputs
        return str(obj)
        
    def _restricted_path(self, *args, **kwargs) -> Path:
        """
        Restricted Path constructor that only allows access to plugin-specific paths.
        
        Returns:
            Restricted Path object
        """
        path = Path(*args, **kwargs)
        
        # Check if this is a plugin-specific path
        # This is a placeholder - actual implementation would validate against
        # allowed plugin directories
        if not self._is_path_allowed(path):
            raise PermissionError(f"Access to path '{path}' is forbidden")
            
        return path
        
    def _is_path_allowed(self, path: Path) -> bool:
        """
        Check if a path is allowed for plugin access.
        
        Args:
            path: Path to check
            
        Returns:
            True if allowed, False otherwise
        """
        # Placeholder implementation
        # In a real implementation, this would check against allowed plugin directories
        # and ensure the path doesn't escape the plugin's sandbox
        
        # Example: only allow paths within the plugin's own directory
        # return plugin_dir in path.parents
        
        # For now, return False to be safe
        return False
        
    def execute_code(self, code: str, local_vars: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute code in the sandbox environment.
        
        Args:
            code: Python code to execute
            local_vars: Additional local variables for execution
            
        Returns:
            Dict of execution results and output
        """
        if local_vars is None:
            local_vars = {}
            
        # Prepare execution environment
        locals_dict = dict(local_vars)
        locals_dict['_print_'] = PrintCollector
        
        # Apply resource limits in a separate thread
        self._apply_resource_limits()
        
        try:
            # Compile the restricted code
            byte_code = compile_restricted(
                code,
                filename='<plugin>',
                mode='exec'
            )
            
            # Execute the code
            exec(byte_code, self.global_scope, locals_dict)
            
            # Extract prints
            printed = locals_dict.get('_print_', None)
            output = printed() if printed else ""
            
            # Remove internal variables from result
            for key in list(locals_dict.keys()):
                if key.startswith('_') and key.endswith('_'):
                    del locals_dict[key]
                    
            return {
                'result': locals_dict,
                'output': output,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error executing plugin code: {str(e)}")
            return {
                'result': {},
                'output': "",
                'error': str(e)
            }
        finally:
            # Reset resource limits
            self._reset_resource_limits()
            
    def _apply_resource_limits(self) -> None:
        """Apply resource limits for plugin execution."""
        # Set memory limit
        if hasattr(resource, 'RLIMIT_AS'):  # Virtual memory limit (not available on all platforms)
            mem_bytes = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            
        # Set CPU time limit
        if hasattr(resource, 'RLIMIT_CPU'):
            resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time, self.max_cpu_time))
            
    def _reset_resource_limits(self) -> None:
        """Reset resource limits after plugin execution."""
        # Reset memory limit
        if hasattr(resource, 'RLIMIT_AS'):
            resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
            
        # Reset CPU time limit
        if hasattr(resource, 'RLIMIT_CPU'):
            resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
```

### 3.2 Permission System

```python
# src/goob_ai/plugin/permissions.py
from typing import Dict, List, Any, Optional, Set
import enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PermissionLevel(enum.Enum):
    """Permission security levels."""
    
    NORMAL = 0     # Safe, no confirmation needed
    SENSITIVE = 1  # Requires user confirmation
    CRITICAL = 2   # Requires user confirmation and warning
    
class Permission(enum.Enum):
    """Available plugin permissions."""
    
    # File system permissions
    READ_APP_FILES = ("read_app_files", PermissionLevel.SENSITIVE, 
                     "Read application files")
    WRITE_APP_FILES = ("write_app_files", PermissionLevel.CRITICAL, 
                      "Write to application files")
    READ_PLUGIN_FILES = ("read_plugin_files", PermissionLevel.NORMAL, 
                       "Read plugin files")
    WRITE_PLUGIN_FILES = ("write_plugin_files", PermissionLevel.NORMAL, 
                        "Write to plugin files")
    
    # Data permissions
    READ_USER_DATA = ("read_user_data", PermissionLevel.SENSITIVE, 
                    "Access user data")
    WRITE_USER_DATA = ("write_user_data", PermissionLevel.CRITICAL, 
                     "Modify user data")
    
    # Network permissions
    NETWORK_ACCESS = ("network_access", PermissionLevel.SENSITIVE, 
                    "Access network resources")
    
    # UI permissions
    MODIFY_UI = ("modify_ui", PermissionLevel.SENSITIVE, 
               "Modify application UI")
    
    # Extension point permissions (examples)
    EXTEND_ANALYSIS = ("extend_analysis", PermissionLevel.NORMAL, 
                     "Add custom analysis capabilities")
    EXTEND_VISUALIZATION = ("extend_visualization", PermissionLevel.NORMAL, 
                          "Add custom visualization capabilities")
    
    def __init__(self, id: str, level: PermissionLevel, description: str) -> None:
        self.id = id
        self.level = level
        self.description = description
        
class PermissionManager:
    """Manages plugin permissions."""
    
    def __init__(self, user_permissions_file: Path) -> None:
        """
        Initialize the permission manager.
        
        Args:
            user_permissions_file: Path to user permissions file
        """
        self.user_permissions_file = user_permissions_file
        self.user_approved_permissions: Dict[str, Set[str]] = self._load_user_permissions()
        
    def _load_user_permissions(self) -> Dict[str, Set[str]]:
        """
        Load user-approved permissions from file.
        
        Returns:
            Dict mapping plugin IDs to sets of approved permission IDs
        """
        import json
        
        if not self.user_permissions_file.exists():
            return {}
            
        try:
            with open(self.user_permissions_file, 'r') as f:
                permissions_dict = json.load(f)
                
            # Convert lists to sets
            return {plugin_id: set(perms) for plugin_id, perms in permissions_dict.items()}
            
        except Exception as e:
            logger.error(f"Error loading user permissions: {str(e)}")
            return {}
            
    def _save_user_permissions(self) -> None:
        """Save user-approved permissions to file."""
        import json
        
        try:
            # Create parent directory if it doesn't exist
            self.user_permissions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert sets to lists for JSON serialization
            permissions_dict = {plugin_id: list(perms) for plugin_id, perms in self.user_approved_permissions.items()}
            
            with open(self.user_permissions_file, 'w') as f:
                json.dump(permissions_dict, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving user permissions: {str(e)}")
            
    def request_permission(self, plugin_id: str, permission: Permission) -> bool:
        """
        Request permission for a plugin.
        
        Args:
            plugin_id: Plugin ID
            permission: Permission to request
            
        Returns:
            True if permission is granted, False otherwise
        """
        # Check if permission is already approved
        if self.has_permission(plugin_id, permission):
            return True
            
        # For automatic approval of NORMAL permissions
        if permission.level == PermissionLevel.NORMAL:
            self.grant_permission(plugin_id, permission)
            return True
            
        # For SENSITIVE and CRITICAL permissions, return False
        # This would be replaced with a UI prompt in the actual implementation
        return False
        
    def grant_permission(self, plugin_id: str, permission: Permission) -> None:
        """
        Grant permission to a plugin.
        
        Args:
            plugin_id: Plugin ID
            permission: Permission to grant
        """
        if plugin_id not in self.user_approved_permissions:
            self.user_approved_permissions[plugin_id] = set()
            
        self.user_approved_permissions[plugin_id].add(permission.id)
        self._save_user_permissions()
        
    def revoke_permission(self, plugin_id: str, permission: Permission) -> None:
        """
        Revoke permission from a plugin.
        
        Args:
            plugin_id: Plugin ID
            permission: Permission to revoke
        """
        if plugin_id in self.user_approved_permissions:
            permissions = self.user_approved_permissions[plugin_id]
            
            if permission.id in permissions:
                permissions.remove(permission.id)
                self._save_user_permissions()
                
    def has_permission(self, plugin_id: str, permission: Permission) -> bool:
        """
        Check if a plugin has a specific permission.
        
        Args:
            plugin_id: Plugin ID
            permission: Permission to check
            
        Returns:
            True if the plugin has the permission, False otherwise
        """
        if plugin_id not in self.user_approved_permissions:
            return False
            
        return permission.id in self.user_approved_permissions[plugin_id]
        
    def get_plugin_permissions(self, plugin_id: str) -> Set[str]:
        """
        Get all permissions granted to a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Set of permission IDs
        """
        return self.user_approved_permissions.get(plugin_id, set())
```

### 3.3 Plugin Security Service

```python
# src/goob_ai/plugin/security.py
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import json
from pathlib import Path
from .sandbox import PluginSandbox
from .permissions import PermissionManager, Permission

logger = logging.getLogger(__name__)

class PluginSecurityService:
    """Service for managing plugin security."""
    
    def __init__(self, permission_manager: PermissionManager) -> None:
        """
        Initialize the plugin security service.
        
        Args:
            permission_manager: Permission manager instance
        """
        self.permission_manager = permission_manager
        self.sandbox = PluginSandbox()
        
    def validate_plugin_package(self, plugin_dir: Path) -> Tuple[bool, List[str]]:
        """
        Validate a plugin package for security.
        
        Args:
            plugin_dir: Plugin directory
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        # Check for manifest
        manifest_path = plugin_dir / "manifest.json"
        if not manifest_path.exists():
            issues.append("Missing manifest.json")
            return False, issues
            
        # Check manifest content
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Check required fields
            required_fields = ['id', 'name', 'version', 'min_app_version']
            for field in required_fields:
                if field not in manifest:
                    issues.append(f"Missing required field '{field}' in manifest")
                    
            # Validate permissions
            if 'permissions' in manifest:
                permissions = manifest['permissions']
                
                if not isinstance(permissions, list):
                    issues.append("Permissions must be a list")
                else:
                    for perm in permissions:
                        if not isinstance(perm, str):
                            issues.append(f"Invalid permission: {perm}")
                        elif not self._is_valid_permission(perm):
                            issues.append(f"Unknown permission: {perm}")
                            
        except json.JSONDecodeError:
            issues.append("Invalid JSON in manifest.json")
        except Exception as e:
            issues.append(f"Error validating manifest: {str(e)}")
            
        # Validate plugin code
        python_files = list(plugin_dir.glob('**/*.py'))
        
        if not python_files:
            issues.append("No Python files found in plugin")
            
        for py_file in python_files:
            file_issues = self._validate_python_file(py_file)
            issues.extend(file_issues)
            
        return len(issues) == 0, issues
        
    def _validate_python_file(self, file_path: Path) -> List[str]:
        """
        Validate a Python file for security issues.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of security issues
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for dangerous imports
            dangerous_imports = [
                'os', 'subprocess', 'sys', 'builtins', 
                'importlib', 'ctypes', 'socket'
            ]
            
            for imp in dangerous_imports:
                if f"import {imp}" in content or f"from {imp}" in content:
                    issues.append(f"Potentially dangerous import: {imp} in {file_path.name}")
                    
            # Check for dangerous functions
            dangerous_functions = [
                'eval(', 'exec(', 'compile(', '__import__('
            ]
            
            for func in dangerous_functions:
                if func in content:
                    issues.append(f"Potentially dangerous function: {func} in {file_path.name}")
                    
        except Exception as e:
            issues.append(f"Error validating {file_path.name}: {str(e)}")
            
        return issues
        
    def _is_valid_permission(self, permission_id: str) -> bool:
        """
        Check if a permission ID is valid.
        
        Args:
            permission_id: Permission ID
            
        Returns:
            True if valid, False otherwise
        """
        try:
            return any(perm.id == permission_id for perm in Permission)
        except:
            return False
            
    def execute_plugin_code(self, plugin_id: str, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute plugin code in the sandbox.
        
        Args:
            plugin_id: Plugin ID
            code: Python code to execute
            context: Execution context
            
        Returns:
            Execution results
        """
        if context is None:
            context = {}
            
        # Add permission checking to context
        def check_permission(permission_id: str) -> bool:
            for perm in Permission:
                if perm.id == permission_id:
                    return self.permission_manager.has_permission(plugin_id, perm)
            return False
            
        context['check_permission'] = check_permission
        
        # Execute code in sandbox
        return self.sandbox.execute_code(code, context)
```

## Integration with Plugin System
The security model integrates with the plugin system through several key components:

1. **Plugin Loading Process**: Before loading a plugin, the application validates the plugin package using the `PluginSecurityService.validate_plugin_package()` method.

2. **Permission Management**: When a plugin requests access to protected resources, the application checks if the plugin has the required permissions using the `PermissionManager.has_permission()` method.

3. **Code Execution**: Plugin code is executed within the sandbox environment using the `PluginSandbox.execute_code()` method, which applies resource constraints and restricts access to sensitive functionality.

```python
# src/goob_ai/services/plugin_service.py
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from ..plugin.registry import PluginRegistry
from ..plugin.manager import PluginManager
from ..plugin.marketplace import PluginMarketplace
from ..plugin.security import PluginSecurityService
from ..plugin.permissions import PermissionManager, Permission

logger = logging.getLogger(__name__)

class PluginService:
    """Service for managing plugins."""
    
    def __init__(self, config_dir: Path, app_version: str) -> None:
        """
        Initialize plugin service.
        
        Args:
            config_dir: Configuration directory
            app_version: Application version
        """
        # Set up directories
        self.config_dir = config_dir
        self.plugins_dir = config_dir / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up components
        self.permission_manager = PermissionManager(config_dir / "plugin_permissions.json")
        self.security_service = PluginSecurityService(self.permission_manager)
        self.registry = PluginRegistry(self.plugins_dir)
        self.manager = PluginManager(self.registry, app_version)
        self.marketplace = PluginMarketplace(self.manager, config_dir)
        
        # Discover available plugins
        self.registry.discover_available_plugins()
        
    def load_enabled_plugins(self) -> Dict[str, bool]:
        """
        Load all enabled plugins.
        
        Returns:
            Dict mapping plugin IDs to load success status
        """
        # First validate all enabled plugins
        enabled_plugins = self.manager.enabled_plugins
        validation_results = {}
        
        for plugin_id in enabled_plugins:
            plugin_dir = self.plugins_dir / plugin_id
            
            if not plugin_dir.exists():
                validation_results[plugin_id] = (False, ["Plugin directory not found"])
            else:
                validation_results[plugin_id] = self.security_service.validate_plugin_package(plugin_dir)
                
        # Load only the plugins that pass validation
        load_results = {}
        
        for plugin_id, (is_valid, issues) in validation_results.items():
            if is_valid:
                success = self.registry.load_plugin(plugin_id)
                load_results[plugin_id] = success
                
                if not success:
                    logger.error(f"Failed to load plugin {plugin_id}")
            else:
                logger.error(f"Plugin {plugin_id} failed validation: {', '.join(issues)}")
                load_results[plugin_id] = False
                
        return load_results
        
    def install_plugin_from_file(self, plugin_file: Path) -> Tuple[bool, str]:
        """
        Install a plugin from a file.
        
        Args:
            plugin_file: Path to plugin file
            
        Returns:
            Tuple of (success, message)
        """
        # Create temporary directory for validation
        import tempfile
        import zipfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Extract plugin package
                if plugin_file.suffix == '.zip':
                    with zipfile.ZipFile(plugin_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)
                else:
                    return False, "Unsupported plugin package format"
                    
                # Validate plugin package
                is_valid, issues = self.security_service.validate_plugin_package(temp_path)
                
                if not is_valid:
                    return False, f"Plugin validation failed: {', '.join(issues)}"
                    
                # If valid, install the plugin
                return self.manager.install_plugin(plugin_file)
                
            except Exception as e:
                logger.error(f"Error installing plugin: {str(e)}")
                return False, f"Error installing plugin: {str(e)}"
                
    def install_plugin_from_repository(self, plugin_id: str, repo_url: str) -> Tuple[bool, str]:
        """
        Install a plugin from a repository.
        
        Args:
            plugin_id: Plugin ID
            repo_url: Repository URL
            
        Returns:
            Tuple of (success, message)
        """
        return self.marketplace.install_plugin_from_repository(plugin_id, repo_url)
        
    def uninstall_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Uninstall a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple of (success, message)
        """
        return self.manager.uninstall_plugin(plugin_id)
        
    def enable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Enable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple of (success, message)
        """
        # First validate the plugin
        plugin_dir = self.plugins_dir / plugin_id
        
        if not plugin_dir.exists():
            return False, f"Plugin {plugin_id} is not installed"
            
        is_valid, issues = self.security_service.validate_plugin_package(plugin_dir)
        
        if not is_valid:
            return False, f"Plugin validation failed: {', '.join(issues)}"
            
        # If valid, enable the plugin
        return self.manager.enable_plugin(plugin_id)
        
    def disable_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """
        Disable a plugin.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Tuple of (success, message)
        """
        return self.manager.disable_plugin(plugin_id)
        
    # ... other plugin-related methods
```

## Implementation Steps

### Week 1: Sandbox Environment (Days 1-3)
1. Create the `PluginSandbox` class for secure code execution
2. Implement resource limiting and isolation
3. Add restricted module access and attribute protection

### Week 2: Permission System & Security Service (Days 4-7)
1. Implement the `PermissionManager` and permission levels
2. Create the plugin validation system
3. Build the security service integration with the plugin system
4. Add runtime monitoring for plugin behavior

## Dependencies
- Python 3.8+
- RestrictedPython (for sandboxed execution)
- jsonschema (for manifest validation)
- resource (built-in, for resource limitation)

## Testing Strategy
1. Security penetration tests to verify sandbox isolation
2. Validation tests with both valid and malicious plugins
3. Permission system tests for different permission levels
4. Resource limit tests to ensure constraints are enforced
5. Integration tests with the plugin system

## Success Criteria
1. Third-party code executes safely without compromising the system
2. Resource usage is effectively limited to prevent abuse
3. Users have clear visibility and control over plugin permissions
4. Malicious plugin code is consistently identified and blocked
5. The security model doesn't significantly impact performance 
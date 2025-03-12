# configmanager.py - ConfigManager class implementation
from modules.utils import *
import os
import json
from pathlib import Path

class ConfigManager:
    """
    Manages application configuration settings.
    Handles saving and loading of user preferences, recent files, and directories.
    """

    def __init__(self, app_name="TotalBattleAnalyzer"):
        """
        Initialize the ConfigManager.
        
        Args:
            app_name (str, optional): The name of the application. Defaults to "TotalBattleAnalyzer".
        """
        self.app_name = app_name
        self.config_dir = os.path.join(os.path.expanduser("~"), ".config", app_name)
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load or create default config
        self.config = self.load_config()
        
    def load_config(self):
        """
        Load configuration from file.
        
        Returns:
            dict: The loaded configuration or default configuration if file doesn't exist.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
        
        # Return default config if loading fails
        return {
            'theme': 'dark',  # Always use dark theme
            'window_size': {'width': 1200, 'height': 800},
            'recent_files': [],
            'max_recent_files': 5,
            'import_dir': os.path.join(os.getcwd(), 'import'),
            'export_dir': os.path.join(os.getcwd(), 'exports')
        }
        
    def save_config(self):
        """Save the current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, section, key, default=None):
        """
        Get a configuration value.
        
        Args:
            section (str): The section name.
            key (str): The key within the section.
            default: The default value to return if the key is not found.
            
        Returns:
            The value for the given key, or the default if not found.
        """
        section_dict = self.config.get(section, {})
        return section_dict.get(key, default)
        
    def set(self, section, key, value):
        """
        Set a configuration value.
        
        Args:
            section (str): The section name.
            key (str): The key within the section.
            value: The value to set.
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()
        
    def add_recent_file(self, filepath):
        """
        Add a file to the recent files list.
        
        Args:
            filepath (str): The path to the file.
        """
        if 'recent_files' not in self.config:
            self.config['recent_files'] = []
            
        # Remove if already exists
        if filepath in self.config['recent_files']:
            self.config['recent_files'].remove(filepath)
            
        # Add to the beginning
        self.config['recent_files'].insert(0, filepath)
        
        # Limit the number of recent files
        max_recent = self.config.get('max_recent_files', 5)
        if len(self.config['recent_files']) > max_recent:
            self.config['recent_files'] = self.config['recent_files'][:max_recent]
            
        self.save_config()
        
    def get_recent_files(self):
        """
        Get the list of recent files.
        
        Returns:
            list: A list of recent file paths.
        """
        return self.config.get('recent_files', [])
        
    def set_theme(self, theme):
        """
        Set the theme (no-op since we only use dark theme).
        
        Args:
            theme (str): The theme name (ignored).
        """
        pass  # No-op since we only use dark theme
        
    def get_theme(self):
        """
        Get the current theme.
        
        Returns:
            str: The theme name (always 'dark').
        """
        return 'dark'  # Always return dark theme
        
    def set_window_size(self, width, height):
        """
        Set the window size.
        
        Args:
            width (int): The window width.
            height (int): The window height.
        """
        self.config['window_size'] = {'width': width, 'height': height}
        self.save_config()
        
    def get_window_size(self):
        """
        Get the window size.
        
        Returns:
            tuple: A tuple of (width, height) as integers.
        """
        size = self.config.get('window_size', {'width': 1200, 'height': 800})
        return int(size['width']), int(size['height'])
        
    def set_import_directory(self, directory):
        """
        Set the import directory.
        
        Args:
            directory (str): The directory path.
        """
        self.config['import_dir'] = directory
        self.save_config()
        
    def get_import_directory(self):
        """
        Get the import directory.
        
        Returns:
            str: The import directory path.
        """
        return self.config.get('import_dir', os.path.join(os.getcwd(), 'import'))
        
    def set_export_directory(self, directory):
        """
        Set the export directory.
        
        Args:
            directory (str): The directory path.
        """
        self.config['export_dir'] = directory
        self.save_config()
        
    def get_export_directory(self):
        """
        Get the export directory.
        
        Returns:
            str: The export directory path.
        """
        return self.config.get('export_dir', os.path.join(os.getcwd(), 'exports'))



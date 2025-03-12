import sys
import traceback

try:
    print("Importing modules.utils...")
    from modules.utils import *
    print("Success!")
    
    print("Importing modules.configmanager...")
    from modules.configmanager import ConfigManager
    print("Success!")
    
    print("Importing modules.stylemanager...")
    from modules.stylemanager import StyleManager
    print("Success!")
    
    print("Importing modules.customtablemodel...")
    from modules.customtablemodel import CustomTableModel
    print("Success!")
    
    print("Importing modules.mplcanvas...")
    from modules.mplcanvas import MplCanvas
    print("Success!")
    
    print("Importing modules.droparea...")
    from modules.droparea import DropArea
    print("Success!")
    
    print("Importing modules.importarea...")
    from modules.importarea import ImportArea
    print("Success!")
    
    print("Importing modules.dataprocessor...")
    from modules.dataprocessor import DataProcessor
    print("Success!")
    
    print("Importing modules.mainwindow...")
    from modules.mainwindow import MainWindow
    print("Success!")
    
    print("All imports successful!")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc() 
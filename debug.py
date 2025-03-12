import traceback
import sys
import os

print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

try:
    # Import the module correctly
    print("Attempting to import module...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("total_battle_analyzer", "src/total-battle-analyzer.py")
    module = importlib.util.module_from_spec(spec)
    print("Module spec created, loading module...")
    spec.loader.exec_module(module)
    print("Module loaded successfully")
    
    # Call the main function
    if hasattr(module, 'main'):
        print("Found main function, attempting to run...")
        module.main()
    elif hasattr(module, 'MainWindow'):
        # Create and run the application directly
        print("Creating PySide6 application...")
        import sys
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        print("Creating MainWindow instance...")
        window = module.MainWindow()
        print("Showing window...")
        window.show()
        print("Starting application event loop...")
        sys.exit(app.exec())
    else:
        print("Could not find main function or MainWindow class")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")
    traceback.print_exc() 
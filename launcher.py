import sys
import os
import traceback

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

core_archive = os.path.join(base_path, "core", "data.dat")

if os.path.exists(core_archive):
    sys.path.insert(0, core_archive)
    
    try:
        from main import MainWindow
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        style_path = os.path.join(base_path, "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
                
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Core loading error:\n{traceback.format_exc()}")
        input("Press Enter to exit...")
else:
    print(f"Core file not found at: {core_archive}")
    input("Press Enter to exit...")
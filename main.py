
import sys
import os

# Ensure src is in path if needed (though local import should work)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import App

if __name__ == "__main__":
    try:
        from ctypes import windll
        myappid = 'romifleur.v2.gui'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    app = App()
    app.run()

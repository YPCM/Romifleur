import sys
import os
import logging

# Ensure src is in path if needed (though local import should work)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from src.app import App
from src.utils.logger import setup_logging

if __name__ == "__main__":
    # Check for debug flag
    debug_mode = "--debug" in sys.argv
    setup_logging(debug_mode=debug_mode)
    
    try:
        try:
            from ctypes import windll
            myappid = 'romifleur.v2.gui'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except ImportError:
            pass
            
        logging.info("Starting Romifleur...")
        app = App()
        app.run()
    except Exception as e:
        logging.critical("Unhandled exception caused crash", exc_info=True)
        sys.exit(1)


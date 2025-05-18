import logging
import os
from datetime import datetime

# Print statements for debugging logger setup itself
# print(f"[LoggerSetup] __file__ is: {__file__}")
_utils_dir = os.path.dirname(os.path.abspath(__file__))
# print(f"[LoggerSetup] _utils_dir: {_utils_dir}")
_retrochat_app_dir = os.path.dirname(_utils_dir)
# print(f"[LoggerSetup] _retrochat_app_dir: {_retrochat_app_dir}")
LOGS_DIR = os.path.join(_retrochat_app_dir, 'logs')
# print(f"[LoggerSetup] LOGS_DIR: {LOGS_DIR}")

if not os.path.exists(LOGS_DIR):
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        # print(f"[LoggerSetup] Created LOGS_DIR: {LOGS_DIR}")
    except Exception as e:
        # print(f"[LoggerSetup] ERROR creating LOGS_DIR {LOGS_DIR}: {e}")
        pass # Avoid crashing if logging dir fails, basicConfig might still work or use root.
# else:
    # print(f"[LoggerSetup] LOGS_DIR {LOGS_DIR} already exists.")

log_file_name = f'retrochat_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
log_file_path = os.path.join(LOGS_DIR, log_file_name)
# print(f"[LoggerSetup] Attempting to log to: {log_file_path}")

# Global flag to enable/disable detailed logging for specific modules
DETAILED_LOGGING_ENABLED = True # Set to False to reduce verbosity


def setup_logging():
    # print("[LoggerSetup] Inside setup_logging()")
    try:
        # Ensure the directory exists one more time, just in case.
        if not os.path.exists(LOGS_DIR):
             os.makedirs(LOGS_DIR, exist_ok=True)
             # print(f"[LoggerSetup] Double-check: Created LOGS_DIR: {LOGS_DIR} from within setup_logging")

        logging.basicConfig(
            level=logging.DEBUG, # Capture all debug messages
            format='%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                # You can also add a StreamHandler to see logs in the console if needed
                # logging.StreamHandler()
            ],
            force=True # Force re-configuration (Python 3.8+)
        )
        # print(f"[LoggerSetup] logging.basicConfig called successfully with force=True for {log_file_path}")
        # Test log
        logging.getLogger("LoggerSetupTest").info("This is a test message from setup_logging after basicConfig(force=True).")
    except Exception as e:
        # print(f"[LoggerSetup] ERROR during logging.basicConfig: {e}")
        # Fallback to console logging if file logging fails (optional)
        # logger = logging.getLogger()
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(logging.DEBUG)
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s')
        # console_handler.setFormatter(formatter)
        # if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        #     logger.addHandler(console_handler)
        #     print("[LoggerSetup] Added fallback StreamHandler to console due to basicConfig error.")
        pass # If logging setup fails, don't crash the app.


setup_logging()
# print("[LoggerSetup] logger_setup.py execution finished.")

# Example of how to get a logger in other modules:
# import logging
# logger = logging.getLogger(__name__)
# logger.debug("This is a debug message.")

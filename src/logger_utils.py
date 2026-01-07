import os
import logging
import json
from datetime import datetime

class DailyLogger:
    def __init__(self, log_dir="logs"):
        base_dir = os.getcwd()
        self.log_dir = os.path.join(base_dir, log_dir)
        self._setup_logger()

    def _setup_logger(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{today}.log")

        self.logger = logging.getLogger("TextToSQL")
        self.logger.setLevel(logging.INFO)
        
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # 1. File Handler (Records EVERYTHING)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', 
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # 2. Console Handler (Only info messages, NO structured dumps)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(file_formatter)
        self.logger.addHandler(self.console_handler)

    def log_info(self, message: str):
        self.logger.info(message)

    def log_error(self, message: str):
        self.logger.error(message)

    def log_struct(self, data: dict, label: str = "EXECUTION_RECORD"):
        """
        Logs structured data to FILE ONLY. 
        Removes console handler temporarily to avoid spamming terminal.
        """
        try:
            if hasattr(data, 'model_dump'):
                data = data.model_dump()
            
            json_str = json.dumps(data, indent=2, default=str)
            log_msg = f"\n[{label}]\n{json_str}\n{'-'*40}"
            
            # Temporarily remove console handler so this only goes to file
            self.logger.removeHandler(self.console_handler)
            self.logger.info(log_msg)
            # Add it back
            self.logger.addHandler(self.console_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to log structured data: {e}")

app_logger = DailyLogger()
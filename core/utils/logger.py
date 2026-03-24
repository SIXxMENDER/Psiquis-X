import logging
import sys
from termcolor import colored

class SafeLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SafeLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger("PsiquisX")
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # Formato compatible con Cloud Logging
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, msg, color="white"):
        self.logger.info(colored(msg, color))

    def warning(self, msg):
        self.logger.warning(colored(msg, "yellow"))

    def error(self, msg):
        self.logger.error(colored(msg, "red"))
    
    def debug(self, msg):
        self.logger.debug(colored(msg, "grey"))

log = SafeLogger()

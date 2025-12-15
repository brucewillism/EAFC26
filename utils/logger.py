"""
Sistema de logging para o bot
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(config=None):
    """Configura o sistema de logging"""
    if config is None:
        config = {}
    
    logger = logging.getLogger("EAFCBot")
    logger.setLevel(getattr(logging, config.get("level", "INFO")))
    
    # Evita duplicar handlers
    if logger.handlers:
        return logger
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se habilitado)
    if config.get("enabled", True):
        log_file = config.get("file", "bot_log.txt")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


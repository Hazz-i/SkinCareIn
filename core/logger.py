# core/logger.py
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("skincarein")

def format_action_log(tag: str, message: str) -> str:
    clean_tag = tag.strip("[]").lower()
    return f"[{clean_tag}] {message}"

def log_action(tag: str, message: str, level: str = "info") -> None:
    formatted = format_action_log(tag, message)
    if level == "error":
        logger.error(formatted)
    elif level == "warning":
        logger.warning(formatted)
    else:
        logger.info(formatted)

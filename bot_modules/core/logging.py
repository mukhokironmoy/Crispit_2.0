import logging
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Define log file path with timestamp
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = log_dir / f"crispit_{now}.log"

# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Silence telegram and httpx low-level logs
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Create a single shared logger
logger = logging.getLogger("crispit_logger")

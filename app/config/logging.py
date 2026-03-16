import logging
from pathlib import Path
from datetime import datetime

# Creating the log directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Creating the log files
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = log_dir / f"crispit_{timestamp}.log"

# Configure the logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Suppress noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.request").setLevel(logging.WARNING)

logger = logging.getLogger("crispit")
import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "ml_service.log"

logger = logging.getLogger("ml_service")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
handler.setFormatter(fmt)
logger.addHandler(handler)

stream = logging.StreamHandler(sys.stdout)
stream.setFormatter(fmt)
logger.addHandler(stream)
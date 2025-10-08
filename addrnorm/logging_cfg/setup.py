import logging, sys, os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(logs_dir: str = "logs", level: str = "INFO") -> logging.Logger:
    os.makedirs(logs_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(logs_dir, f"addrnorm_{ts}.log")

    logger = logging.getLogger("addrnorm")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.log_path = log_path  # <- добавили
    logger.info("Logger initialized → %s", log_path)
    return logger

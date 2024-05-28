import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)-7s %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

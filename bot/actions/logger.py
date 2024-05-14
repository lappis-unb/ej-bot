import json
import logging

logger = logging.getLogger(__name__)


def custom_logger(message, data={}, _type="json"):
    format = f"EJ INTEGRATION DEBUGGING - {message}"
    if _type == "json" and data:
        logger.debug(f"{format}: \n {json.dumps(data, indent=4)}")
    else:
        logger.debug(f"{format}")

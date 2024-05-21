"""retry"""

import time
from typing import Callable
from loguru import logger


# pylint: disable=broad-exception-caught
def retry(func: Callable, *args, max_retries=3, delay=0.1):
    """call a function with max retries"""

    for attempt in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            logger.info(f"{func} Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)  # Wait before retrying
                continue

            logger.error(f"{func} Max retries reached. Function failed.")
            raise  # Re-raise the exception after the final attempt

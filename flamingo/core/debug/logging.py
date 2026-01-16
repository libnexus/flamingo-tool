import io
import logging

log_capture_string = io.StringIO()

_capture_handler = logging.StreamHandler(log_capture_string)
_capture_handler.setLevel(logging.DEBUG)
_formatter = logging.Formatter('%(asctime)s | %(name)-10s | %(levelname)-7s | %(message)s', datefmt='%H:%M:%S')
_capture_handler.setFormatter(_formatter)

logger = logging.getLogger('flamingo')
logger.setLevel(logging.DEBUG)
logger.addHandler(_capture_handler)


# TODO: Add file handler if needed later
# _file_handler = logging.FileHandler('flamingo.debug.log')
# logger.addHandler(_file_handler)

def get_recent_logs(limit=100):
    """Retrieves the last N lines from the in-memory buffer."""
    content = log_capture_string.getvalue()
    lines = content.splitlines()
    return lines[-limit:]

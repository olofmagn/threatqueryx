import logging

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

# Application Configuration
DEFAULT_MODE = "qradar"
DEFAULT_ENCODING = "utf-8"
DEFAULT_TIME_RANGE_INDEX = 1  # "10 MINUTES"
PLATFORMS = ["qradar", "defender", "elastic"]
DEFAULT_LOGGER_NAME = "ThreatQueryX"
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Window Configuration
DEFAULT_WINDOW_WIDTH = 500
DEFAULT_WINDOW_HEIGHT = 400
DEFAULT_OUTPUT_HEIGHT = 10
DEFAULT_PADDING = 10
OUTPUT_FRAME_PADDING = 5
WINDOW_PADDING = 10
WINDOW_TITLE = "ThreatQueryX - Multi-Platform Threat Hunting Query Builder"
COMBOBOX_WIDTH = 25
FRAME_SIZE_MINIMUM = 100

# Grid Positioning Constants
GRID_STICKY_EW = "ew"
GRID_STICKY_NSEW = "nsew"
GRID_STICKY_E = "e"

# UI Text Constants
COPYRIGHT_TEXT = "© 2025 olofmagn"
COPYRIGHT_FONT = ("Segoe UI", 8, "italic")
COPYRIGHT_COLOR = "gray50"

# Widget Styling Constants
WIDGET_PADDING_X = 5
WIDGET_PADDING_Y = 5
TIME_ENTRY_WIDTH = 15
ARROW_BUTTON_WIDTH = 2
ARROW_BUTTON_PADDING = (6, 0)

# Valid Platforms
VALID_PLATFORMS = {
    "defender": {"description": "Microsoft Defender for Endpoint"},
    "elastic": {"description": "Elastic SIEM"},
    "qradar": {"description": "IBM QRadar"},
}

# Time Range Configuration
TIME_RANGES = [
    ("5m", "5 MINUTES"),
    ("10m", "10 MINUTES"),
    ("30m", "30 MINUTES"),
    ("1h", "1 HOUR"),
    ("3h", "3 HOURS"),
    ("12h", "12 HOURS"),
    ("1d", "1 DAY"),
]

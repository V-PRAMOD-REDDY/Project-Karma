# Configuration Constants

# Camera Settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# AI Settings
CONFIDENCE_THRESHOLD = 0.4
MODEL_PATH = 'yolov8n.pt'  # Will download automatically

# Analytic Thresholds
PANIC_VELOCITY_THRESHOLD = 20.0  # Pixels per frame movement
HEATMAP_INTENSITY = 0.05         # How fast the heatmap turns red

# Colors (BGR Format)
COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
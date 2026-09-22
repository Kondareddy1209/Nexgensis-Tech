"""Unit and integration tests for FastBox Delivery Simulator."""

import sys
from pathlib import Path

# Ensure the project root is in sys.path for test discovery from any directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

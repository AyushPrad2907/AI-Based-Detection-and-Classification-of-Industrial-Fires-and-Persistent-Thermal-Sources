"""
SIH26162 Backend Application Package.

FastAPI-based backend for Industrial Fire & Thermal AI Detector.
"""

import sys
from pathlib import Path

# Ensure 'backend' directory and repository root are present in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(1, str(_REPO_ROOT))

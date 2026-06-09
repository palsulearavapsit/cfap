import sys
import os

# Append project root directory to python sys.path for backend resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

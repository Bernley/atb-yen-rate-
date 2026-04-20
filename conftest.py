import sys
import os

# Ensure the project root is first on sys.path so that our local parser.py
# takes precedence over the deprecated built-in `parser` module (Python 3.9).
sys.path.insert(0, os.path.dirname(__file__))

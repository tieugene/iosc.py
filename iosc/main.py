#!/usr/bin/env python3
"""Application entry module."""
import os.path
import sys

if __name__ == "__main__":
    if 'PYTHONPATH' not in os.environ:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from mainwindow import main
    sys.exit(main())

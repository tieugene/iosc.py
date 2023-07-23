#!/usr/bin/env python3
"""Application entry module."""
import os
import sys
import pathlib

if __name__ == "__main__":
    if 'PYTHONPATH' not in os.environ:
        sys.path.append(pathlib.Path(__file__).resolve().parent.parent.as_posix())
    from iosc.mainwindow import main
    sys.exit(main())

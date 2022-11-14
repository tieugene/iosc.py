"""Circular Vector Diagram"""
# 2. 3rd
from PyQt5.QtWidgets import QDialog


class CVDWindow(QDialog):
    """Main CVD window.
    RTFM: Qt examples/widgets/windowsflags.py
    Buttons:
    - close
    - expand/restore
    - menu:
      + Settings
      + Time:
        * MainPtr
        * Tx[]
    """
    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)

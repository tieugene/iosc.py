#!/usr/bin/env python3
# 1. std
import sys
# 2. 3rd
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt, QCoreApplication
# 3. local
from view import MainWindow


def main():
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication()
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

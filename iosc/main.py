#!/usr/bin/env python3
# 1. std
import sys
# 2. 3rd
from PySide2.QtWidgets import QApplication, QMainWindow
# 3. local
from mainwindow import MainWindow


def main():
    # QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    mw: QMainWindow = MainWindow()
    available_geometry = app.desktop().availableGeometry(mw)  # 0, 0, 1280, 768 (display height - taskbar)
    mw.resize(available_geometry.width() * 3 / 4, available_geometry.height() * 3 / 4)
    mw.show()
    mw.handle_cli()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

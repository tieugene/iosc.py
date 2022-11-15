"""Circular Vector Diagram"""
import math

from PyQt5.QtCore import Qt, QRectF, QPoint, QPointF
from PyQt5.QtGui import QIcon, QResizeEvent, QPainter, QPen, QColor
# 2. 3rd
from PyQt5.QtWidgets import QDialog, QTableWidget, QAction, QVBoxLayout, QToolBar, QSplitter, QGraphicsView, \
    QGraphicsScene, QGraphicsObject, QStyleOptionGraphicsItem, QWidget, QGraphicsEllipseItem, QGraphicsLineItem

# x. consts
RAD = 100  # Radius of diagram
GRID_STEPS_C = 5  # Number of circular grid lines
GRID_STEPS_R = 8  # Number of radial grid lines
POINT_Z = QPoint(0, 0)  # Helper


class CVDiagramObject(QGraphicsObject):
    class GridC(QGraphicsEllipseItem):
        def __init__(self, radius: int, parent: 'CVDiagramObject'):
            super().__init__(-radius, -radius, 2 * radius, 2 * radius, parent)

    class GridR(QGraphicsLineItem):
        def __init__(self, angle: float, parent: 'CVDiagramObject'):
            super().__init__(0, 0, RAD * math.sin(angle), RAD * math.cos(angle), parent)

    def __init__(self):
        super().__init__()
        # grid
        pen = QPen(Qt.gray)
        pen.setCosmetic(True)  # don't change width on resizing
        for i in range(GRID_STEPS_C):  # - circular
            self.GridC(RAD - RAD // GRID_STEPS_C * i, self).setPen(pen)
        for i in range(GRID_STEPS_R):  # radial
            self.GridR(i * math.radians(360 // GRID_STEPS_R), self).setPen(pen)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # auto


class CVDiagramView(QGraphicsView):
    circle: CVDiagramObject

    def __init__(self, parent: 'CVDWindow'):
        # Howto (resize to content): scene.setSceneRect(scene.itemsBoundingRect()) <= QGraphicsScene::changed()
        super().__init__(parent)
        self.setScene(QGraphicsScene())
        # self.setMinimumSize(100, 100)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.circle = CVDiagramObject()
        self.scene().addItem(self.circle)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)


class CVTable(QTableWidget):
    def __init__(self, parent: 'CVDWindow'):
        super().__init__(parent)
        self.setColumnCount(6)
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalHeaderLabels(("№", "Name", "Module", "Angle", "Re", "Im"))
        self.resizeRowsToContents()


class CVDWindow(QDialog):
    """Main CVD window."""
    toobar: QToolBar
    diagram: CVDiagramView
    table: CVTable
    action_settings: QAction
    action_select_ptr: QAction
    action_close: QAction

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_toolbar()
        self.setWindowTitle("Vector Diagram")

    def __mk_widgets(self):
        self.toolbar = QToolBar(self)
        self.diagram = CVDiagramView(self)
        self.table = CVTable(self)

    def __mk_layout(self):
        """Layout:
        - toolbar
        - plot
        - table
        """
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.diagram)
        splitter.addWidget(self.table)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(splitter)

    def __mk_actions(self):
        self.action_settings = QAction(QIcon.fromTheme("document-properties"),
                                       "&Settings",
                                       self,
                                       triggered=self.__do_settings)
        self.action_select_ptr = QAction(QIcon.fromTheme("go-jump"),
                                         "&Pointer",
                                         self,
                                         triggered=self.__do_select_ptr)
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    triggered=self.close)

    def __mk_toolbar(self):
        self.toolbar.addAction(self.action_settings)
        self.toolbar.addAction(self.action_select_ptr)
        self.toolbar.addAction(self.action_close)

    def __do_settings(self):
        ...

    def __do_select_ptr(self):
        # Mainptr[, TmpPtr[]]
        ...

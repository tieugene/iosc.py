"""Circular Vector Diagram"""
import math
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPoint, QPointF, QSizeF, QLineF
from PyQt5.QtGui import QIcon, QResizeEvent, QPainter, QPen, QColor, QFont, QPolygonF
# 2. 3rd
from PyQt5.QtWidgets import QDialog, QTableWidget, QAction, QVBoxLayout, QToolBar, QSplitter, QGraphicsView, \
    QGraphicsScene, QGraphicsObject, QStyleOptionGraphicsItem, QWidget, QGraphicsEllipseItem, QGraphicsLineItem, \
    QGraphicsTextItem

# x. consts
RAD = 100  # Radius of diagram
DRAD_AXIS_LABEL = 5
ARROW_SIZE = 10
ARROW_ANGLE = math.pi / 6
GRID_STEPS_C = 5  # Number of circular grid lines
GRID_STEPS_R = 8  # Number of radial grid lines
POINT_Z = QPointF(0, 0)  # Helper
SIN225 = math.sin(math.pi / 8)  # 22.5°


def sign(v: float):
    if abs(v) < SIN225:
        return 0
    elif v < 0:
        return -1
    else:
        return 1


class CVDiagramObject(QGraphicsObject):
    class GridC(QGraphicsEllipseItem):
        def __init__(self, parent: 'CVDiagramObject', radius: int):
            super().__init__(-radius, -radius, 2 * radius, 2 * radius, parent)

    class GridR(QGraphicsLineItem):
        def __init__(self, parent: 'CVDiagramObject', angle: float):
            super().__init__(0, 0, RAD * math.cos(angle), RAD * math.sin(angle), parent)

    class Label(QGraphicsTextItem):
        def __init__(self, parent: 'CVDiagramObject', text: str, a: float, r: float, color: Optional[QColor] = None):
            super().__init__(text, parent)
            self.setFont(QFont('mono', 8))
            if color is not None:
                self.setDefaultTextColor(color)
            self.adjustSize()
            x0_norm, y0_norm = math.cos(a), math.sin(a)
            rect: QRectF = self.boundingRect()
            self.setPos(QPointF(
                (r + DRAD_AXIS_LABEL) * x0_norm + (sign(x0_norm) - 1) * rect.width() / 2,
                (r + DRAD_AXIS_LABEL) * y0_norm + (sign(y0_norm) - 1) * rect.height() / 2
            ))

    class Arrow(QGraphicsLineItem):
        __angle: float
        __len: float
        __arrowHead: QPolygonF

        def __init__(self, parent: 'CVDiagramObject', a: float, r: float):
            super().__init__(parent)
            self.__angle = a
            self.__len = r
            self.__arrowHead = QPolygonF()

        def boundingRect(self):
            xtra = self.pen().width() / 2 + ARROW_SIZE * math.sin(ARROW_ANGLE)
            p1 = self.line().p1()
            p2 = self.line().p2()
            return QRectF(p1, QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-xtra, -xtra, xtra, xtra)

        def shape(self):
            path = super().shape()
            path.addPolyline(self.__arrowHead)
            return path

        def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
            # super().paint(painter, option, widget)
            e = QPointF(self.__len * math.cos(self.__angle), self.__len * math.sin(self.__angle))
            self.setLine(QLineF(POINT_Z, e))
            arrow_l = self.line().p2() + QPointF(-math.cos(self.__angle + ARROW_ANGLE) * ARROW_SIZE,
                                                 -math.sin(self.__angle + ARROW_ANGLE) * ARROW_SIZE)
            arrow_r = self.line().p2() + QPointF(-math.cos(self.__angle - ARROW_ANGLE) * ARROW_SIZE,
                                                 -math.sin(self.__angle - ARROW_ANGLE) * ARROW_SIZE)
            self.__arrowHead.clear()
            for point in [arrow_l, self.line().p2(), arrow_r]:
                self.__arrowHead.append(point)
            painter.drawLine(self.line())
            painter.drawPolyline(self.__arrowHead)

    def __init__(self):
        super().__init__()
        # grid
        pen = QPen(Qt.gray)
        pen.setCosmetic(True)  # don't change width on resizing
        for i in range(GRID_STEPS_C):  # - circular
            self.GridC(self, RAD - RAD // GRID_STEPS_C * i).setPen(pen)
        for i in range(GRID_STEPS_R):  # - radial
            self.GridR(self, i * math.radians(360 // GRID_STEPS_R)).setPen(pen)
        # axes labels
        pen.setColor(Qt.black)
        self.Label(self, "90°", 0, RAD)
        self.Label(self, "180°", math.pi / 2, RAD)
        self.Label(self, "-90°", math.pi, RAD)
        self.Label(self, "0°", -math.pi / 2, RAD)
        # for i in range(12):  # test
            # self.Label(self, f"L{i * 10}", math.pi / 6, RAD, QColor(Qt.black))
            # self.Arrow(self, i * math.pi / 6, RAD * 2 / 3)

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub


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

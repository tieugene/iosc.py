"""Circular Vector Diagram"""
import cmath
import math
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QLineF
from PyQt5.QtGui import QIcon, QResizeEvent, QPainter, QPen, QColor, QFont, QPolygonF, QPixmap
# 2. 3rd
from PyQt5.QtWidgets import QDialog, QTableWidget, QAction, QVBoxLayout, QToolBar, QSplitter, QGraphicsView, \
    QGraphicsScene, QGraphicsObject, QStyleOptionGraphicsItem, QWidget, QGraphicsEllipseItem, QGraphicsLineItem, \
    QGraphicsTextItem, QComboBox, QLabel, QTableWidgetItem

from iosc.core.sigfunc import hrm1
from iosc.sig.widget.common import AnalogSignalSuit
from iosc.sig.widget.dialog import SelectSignalsDialog

# x. consts
RAD = 100  # Radius of diagram
DRAD_AXIS_LABEL = 0  # Distance from end of line to label margin
ARROW_SIZE = 10  # Arrow sides length
ARROW_ANGLE = math.pi / 6  # Arrow sides angle from main line
GRID_STEPS_C = 5  # Number of circular grid lines
GRID_STEPS_R = 8  # Number of radial grid lines
POINT_Z = QPointF(0, 0)  # Helper
SIN225 = math.sin(math.pi / 8)  # 22.5°
TABLE_HEAD = ("Name", "Module", "Angle", "Re", "Im")


def sign(v: float):
    if abs(v) < SIN225:
        return 0
    elif v < 0:
        return -1
    else:
        return 1


class SelectCVDSignalsDialog(SelectSignalsDialog):
    f_base_signal: QComboBox

    def __init__(
            self,
            ass_list: list[AnalogSignalSuit],
            ass_used: set[int],
            ass_base: Optional[int],
            parent=None
    ):
        super().__init__(ass_list, ass_used, parent)
        self.f_base_signal = QComboBox(self)
        self.f_base_signal.addItem('---')
        for i, ss in enumerate(ass_list):
            pixmap = QPixmap(16, 16)
            pixmap.fill(ss.color)
            self.f_base_signal.addItem(QIcon(pixmap), ss.signal.sid)
        if ass_base is not None:
            self.f_base_signal.setCurrentIndex(ass_base + 1)
        self.layout().insertWidget(2, QLabel("Base:", self))
        self.layout().insertWidget(3, self.f_base_signal)

    def execute(self) -> Optional[tuple[list[int], Optional[int]]]:
        """
        :return: None if Cancel, list of selected items if ok
        """
        if self.exec_():
            retlist = list()
            for i in range(self.f_signals.count()):
                if self.f_signals.item(i).checkState() == Qt.Checked:
                    retlist.append(i)
            if retval := self.f_base_signal.currentIndex():
                retval -= 1
            else:
                retval = None
            return retlist, retval


class CVDiagramObject(QGraphicsObject):
    class GridC(QGraphicsEllipseItem):
        def __init__(self, parent: 'CVDiagramObject', radius: int):
            super().__init__(-radius, -radius, 2 * radius, 2 * radius, parent)

    class GridR(QGraphicsLineItem):
        def __init__(self, parent: 'CVDiagramObject', angle: float):
            super().__init__(0, 0, RAD * math.cos(angle), RAD * math.sin(angle), parent)

    class Label(QGraphicsTextItem):
        def __init__(self, parent: QGraphicsObject, text: str, a: float, r: float, color: Optional[QColor] = None):
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

        def __init__(self, parent: QGraphicsObject, a: float, r: float):
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
            path.addPolygon(self.__arrowHead)
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

    class SigVector(QGraphicsObject):
        __arrow: 'CVDiagramObject.Arrow'
        __label: 'CVDiagramObject.Label'

        def __init__(self, parent: QGraphicsObject, text: str, a: float, r: float):
            super().__init__(parent)
            self.__arrow = CVDiagramObject.Arrow(self, a, r)
            self.__label = CVDiagramObject.Label(self, text, a, r)

        def boundingRect(self) -> QRectF:
            return self.childrenBoundingRect()

        def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
            ...  # stub

        def set_color(self, c: QColor):
            pen = self.__arrow.pen()
            pen.setColor(c)  # FIXME: not works
            self.__arrow.setPen(pen)  # FIXME: .setCosmetic(True)
            self.__label.setDefaultTextColor(c)

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
        #    # self.Label(self, f"L{i}", math.pi / 6, RAD, QColor(Qt.black))
        #    # self.Arrow(self, i * math.pi / 6, RAD * 2 / 3)
        #    # self.SigVector(self, f"L{i}", i * math.pi / 6, RAD * 2 / 3)

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub


class CVDiagramView(QGraphicsView):
    __parent: 'CVDWindow'
    circle: CVDiagramObject

    def __init__(self, parent: 'CVDWindow'):
        # Howto (resize to content): scene.setSceneRect(scene.itemsBoundingRect()) <= QGraphicsScene::changed()
        super().__init__(parent)
        self.__parent = parent
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

    def reload_signals(self):
        """Reload vectors from selected signals."""
        pen = QPen()
        pen.setCosmetic(True)
        i = self.__parent.t_i
        for r, ss in enumerate(self.__parent.ss_used):
            v: complex = ss.hrm1(i)
            CVDiagramObject.SigVector(self.circle, ss.signal.sid, cmath.phase(v), RAD).set_color(ss.color)

    def refresh_signals(self):
        """Refresh row values by ptr"""


class CVTable(QTableWidget):
    __parent: 'CVDWindow'

    def __init__(self, parent: 'CVDWindow'):
        super().__init__(parent)
        self.__parent = parent
        self.setColumnCount(len(TABLE_HEAD))
        self.horizontalHeader().setStretchLastSection(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalHeaderLabels(TABLE_HEAD)
        self.setSelectionMode(self.NoSelection)
        self.resizeRowsToContents()

    def reload_signals(self):
        """Reload rows from selected signals."""
        self.setRowCount(len(self.__parent.ss_used))  # all items can be None
        for r, ss in enumerate(self.__parent.ss_used):
            for c in range(self.columnCount()):
                if self.item(r, c) is None:
                    self.setItem(r, c, QTableWidgetItem())
                    if c:
                        self.item(r, c).setTextAlignment(Qt.AlignRight)
            self.item(r, 0).setCheckState(Qt.Checked)
            self.item(r, 0).setText(ss.signal.sid)
            self.item(r, 0).setForeground(ss.color)
        self.refresh_signals()
        self.resizeColumnsToContents()

    def refresh_signals(self):
        """Refresh row values by ptr"""
        i = self.__parent.t_i
        for r, ss in enumerate(self.__parent.ss_used):
            v: complex = ss.hrm1(i)
            uu = ss.signal.raw2.uu
            self.item(r, 1).setText("%.1f %s" % (abs(v), uu))
            self.item(r, 2).setText("%.1f°" % math.degrees(cmath.phase(v)))
            self.item(r, 3).setText("%.1f %s" % (v.real, uu))
            self.item(r, 4).setText("%.1f %s" % (v.imag, uu))


class CVDWindow(QDialog):
    """Main CVD window."""
    __ass_list: list[AnalogSignalSuit]  # just shortcut
    ss_used: list[AnalogSignalSuit]
    ss_base: Optional[AnalogSignalSuit]
    toobar: QToolBar
    diagram: CVDiagramView
    table: CVTable
    action_settings: QAction
    action_select_ptr: QAction
    action_close: QAction

    def __init__(self, parent: 'ComtradeWidget'):
        super().__init__(parent)
        self.__ass_list = parent.ass_list
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_toolbar()
        self.setWindowTitle("Vector Diagram")
        self.ss_used = list()
        self.ss_base = None

    @property
    def t_i(self):
        """Current MainPtr.i"""
        return self.parent().main_ptr_i

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
                                       shortcut="Ctrl+S",
                                       triggered=self.__do_settings)
        self.action_select_ptr = QAction(QIcon.fromTheme("go-jump"),
                                         "&Pointer",
                                         self,
                                         triggered=self.__do_select_ptr)
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    shortcut="Ctrl+W",
                                    triggered=self.close)

    def __mk_toolbar(self):
        self.toolbar.addAction(self.action_settings)
        self.toolbar.addAction(self.action_select_ptr)
        self.toolbar.addAction(self.action_close)

    def __do_settings(self):
        ss_used_i = set([ss.signal.i for ss in self.ss_used])  # WARN: works if ss.signal.i <=> self.__ass_list[i]
        ss_base_i = self.ss_base.signal.i if self.ss_base else None
        retvalue = SelectCVDSignalsDialog(self.__ass_list, ss_used_i, ss_base_i).execute()
        if retvalue is not None:
            self.ss_used.clear()
            self.ss_used = [self.__ass_list[i] for i in retvalue[0]]
            self.ss_base = self.__ass_list[retvalue[1]] if retvalue[1] is not None else None
            self.table.reload_signals()
            self.diagram.reload_signals()

    def __do_select_ptr(self):
        # Mainptr[, TmpPtr[]]
        ...

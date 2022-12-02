import cmath
import math
from typing import Optional

from PyQt5.QtCore import QRectF, QPointF, QSizeF, QLineF, Qt
from PyQt5.QtGui import QColor, QFont, QPolygonF, QPainter, QPen
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, \
    QStyleOptionGraphicsItem, QWidget

from iosc.sig.tools.util import sign_b2n
from iosc.sig.widget.common import AnalogSignalSuit

# x. consts
RAD = 100  # Radius of chart
DRAD_AXIS_LABEL = 0  # Distance from end of line to label margin
ARROW_SIZE = 10  # Arrow sides length
ARROW_ANGLE = math.pi / 6  # Arrow sides angle from main line
GRID_STEPS_C = 5  # Number of circular grid lines
GRID_STEPS_R = 8  # Number of radial grid lines
POINT_Z = QPointF(0, 0)  # Helper
SIN225 = math.sin(math.pi / 8)  # 22.5°


class CVDiagramObject(QGraphicsObject):
    class GridC(QGraphicsEllipseItem):
        def __init__(self, parent: 'CVDiagramObject', radius: int):
            super().__init__(-radius, -radius, 2 * radius, 2 * radius, parent)

    class GridR(QGraphicsLineItem):
        def __init__(self, parent: 'CVDiagramObject', angle: float):
            super().__init__(0, 0, RAD * math.cos(angle), RAD * math.sin(angle), parent)

    class Label(QGraphicsTextItem):
        __angle: float
        __len: float

        def __init__(self, parent: QGraphicsObject, text: str, a: float, r: float, color: Optional[QColor] = None):
            super().__init__(text, parent)
            self.__len = r
            self.setFont(QFont('mono', 8))
            if color is not None:
                self.set_color(color)
            self.adjustSize()
            self.set_angle(a)

        def set_angle(self, a: float):
            ...  # TODO:
            self.__angle = a
            x0_norm, y0_norm = math.cos(a), math.sin(a)
            rect: QRectF = self.boundingRect()
            self.setPos(QPointF(
                (self.__len + DRAD_AXIS_LABEL) * x0_norm + (sign_b2n(x0_norm, SIN225) - 1) * rect.width() / 2,
                (self.__len + DRAD_AXIS_LABEL) * y0_norm + (sign_b2n(y0_norm, SIN225) - 1) * rect.height() / 2
            ))

        def set_color(self, c: QColor):
            self.setDefaultTextColor(c)

    class Arrow(QGraphicsLineItem):
        __angle: float
        __len: float
        __color: QColor
        __arrowHead: QPolygonF

        def __init__(self, parent: QGraphicsObject, a: float, r: float, color: Optional[QColor] = None):
            super().__init__(parent)
            self.__angle = a
            self.__len = r
            self.__color = color
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
            if self.__color:
                pen = QPen(self.__color)
                pen.setCosmetic(True)
                painter.setPen(pen)
            painter.drawLine(self.line())
            painter.drawPolyline(self.__arrowHead)

        def set_angle(self, a: float):
            self.__angle = a

        def set_color(self, c: QColor):  # FIXME: repaint?
            self.__color = c

    class SigVector(QGraphicsObject):
        __parent: 'CVDiagramObject'
        __ss: AnalogSignalSuit
        __arrow: 'CVDiagramObject.Arrow'
        __label: 'CVDiagramObject.Label'

        def __init__(self, parent: 'CVDiagramObject', ss: AnalogSignalSuit):
            super().__init__(parent)
            self.__parent = parent
            self.__ss = ss
            angle = self.__get_angle()
            pen = QPen(self.__ss.color)
            pen.setCosmetic(True)
            self.__arrow = CVDiagramObject.Arrow(self, angle, RAD, self.__ss.color)
            self.__label = CVDiagramObject.Label(self, self.__ss.signal.sid, angle, RAD, self.__ss.color)
            self.__ss.signal_chg_color.connect(self.__slot_update_color)

        def boundingRect(self) -> QRectF:
            return self.childrenBoundingRect()

        def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
            ...  # stub

        def __get_angle(self) -> float:
            return \
                cmath.phase(self.__ss.hrm(1, self.__parent.cvdview.cvdwin.t_i)) \
                - self.__parent.cvdview.cvdwin.get_base_angle() \
                - math.pi / 2

        def __slot_update_color(self):
            self.__arrow.set_color(self.__ss.color)
            self.__label.set_color(self.__ss.color)

        def update_angle(self):
            a = self.__get_angle()
            self.__arrow.set_angle(a)
            self.__label.set_angle(a)  # ? refreshes arrow ?

    cvdview: 'CVDiagramView'
    sv_list: list[SigVector]

    def __init__(self, cvdview: 'CVDiagramView'):
        super().__init__()
        self.cvdview = cvdview
        self.sv_list = list()
        # grid
        pen = QPen(Qt.gray)
        pen.setCosmetic(True)  # don't change width on resizing
        for i in range(GRID_STEPS_C):  # - circular
            self.GridC(self, RAD - RAD // GRID_STEPS_C * i).setPen(pen)
        for i in range(GRID_STEPS_R):  # - radial
            self.GridR(self, i * math.radians(360 // GRID_STEPS_R)).setPen(pen)
        # axes labels
        pen.setColor(Qt.black)
        self.Label(self, "-90°", 0, RAD)
        self.Label(self, "180°", math.pi / 2, RAD)
        self.Label(self, "+90°", math.pi, RAD)
        self.Label(self, "0°", -math.pi / 2, RAD)

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub

    def sv_clean(self):
        """Clean signal vectors"""
        for sv in self.sv_list:
            sv.deleteLater()
        self.sv_list.clear()

    def sv_add(self, ss: AnalogSignalSuit):
        """Add signal vector"""
        self.sv_list.append(self.SigVector(self, ss))

    def sv_refresh(self):
        for sv in self.sv_list:
            sv.update_angle()

    def sv_show(self, i: int, show: bool):
        self.sv_list[i].setVisible(show)

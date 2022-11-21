"""
1 dot = .1"
"""
from PyQt5.QtCore import QRectF
# 2. 3rd
from PyQt5.QtGui import QPainter, QFont, QPageLayout
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QAction, QGraphicsTextItem, QGraphicsRectItem, \
    QGraphicsLineItem, QGraphicsSimpleTextItem, QGraphicsItem, QWidget, QStyleOptionGraphicsItem
# 3. local
from iosc.core import mycomtrade
from iosc.sig.widget.common import AnalogSignalSuit

# x. const
A4 = (748, 1130)  # (w, h) of A4 - 10mm margins in "dots" (0.01")
H_ASIG = (176, 112)  # H of analog signal
H_SCALE = 20
W_COL0 = 112  # W of 1st column
MAIN_FONT = QFont('Source Code Pro', 8)  # 14x6 "dots"


class HeaderItem(QGraphicsSimpleTextItem):
    def __init__(self, osc: mycomtrade.MyComtrade, parent=None):
        super().__init__(  # 14 dots per line
            f"{osc.path.name}"
            f"\nStart time: {osc.raw.start_timestamp.isoformat()}"
            f"\nDevice: {osc.raw.rec_dev_id}, Place: {osc.raw.station_name}",
            parent
        )
        self.setFont(MAIN_FONT)


class TableItem(QGraphicsRectItem):
    def __init__(self, w: int, h: int, parent=None):
        super().__init__(0, 0, w, h - 0.5, parent)  # 1. border
        QGraphicsLineItem(W_COL0, 0, W_COL0, h - 0.5, self)  # 2. columns separator
        QGraphicsLineItem(0, h - H_SCALE, w, h - H_SCALE, self)  # 3. underscore
        # 4. TODO: grid


class SignalItem(QGraphicsItem):
    __signal: mycomtrade.Signal

    def __init__(self, signal: mycomtrade.Signal, parent=None):
        super().__init__(parent)
        self.__signal = signal

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()  # H == plot height, W = underscore

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub


class PrintRender(QGraphicsView):
    __to_print: list[bool]

    def __init__(self, parent='ComtradeWidget'):
        super().__init__(parent)
        self.__to_print = [False] * 5
        self.setScene(QGraphicsScene())

    def slot_set_to_print(self, a: QAction):
        """Slot """
        self.__to_print[a.data()] = a.isChecked()

    def print_(self, printer: QPrinter):
        """
        Use printer.pageRect(QPrinter.Millimeter/DevicePixel).
        Use:
        - printer.pageLayout().orientation() (QPageLayout::Portrait/Landscape)
        - self.parent().xscroll_bar.{norm_min,norm_max}
        :param printer: Where to draw to
        # FIXME: clean on replot (?)
        # TODO: while(signals) plot | pagebreak
        """
        self.scene().clear()
        # xsb = self.parent().xscroll_bar
        # print(xsb.norm_min, xsb.norm_max)
        if printer.pageLayout().orientation() == QPageLayout.Portrait:
            w_all, h_all = A4[0], A4[1]
        else:
            w_all, h_all = A4[1], A4[0]
        # fill
        osc: mycomtrade.MyComtrade = self.parent().osc
        # - header
        self.scene().addItem(h := HeaderItem(osc))
        y = round(h.boundingRect().height())
        # - table
        self.scene().addItem(t := TableItem(w_all, h_all - y))
        t.setPos(0, y)
        # - signals
        for signal in osc.y:
            s_item = SignalItem(signal)
        # output
        print(self.scene().itemsBoundingRect().height())  # 670.5
        self.scene().setSceneRect(self.scene().itemsBoundingRect())
        # self.render(QPainter(printer))  # Plan A. Sizes: dst: printer.pageSize(), src: self.viewport().rect()
        self.scene().render(QPainter(printer))  # Sizes: dst: printer.pageSize(), src: self.scene().sceneRect()

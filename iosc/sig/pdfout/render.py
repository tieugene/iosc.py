"""
1 dot = .1"
TODO: just resize items on page change
"""
from PyQt5.QtCore import QRectF
# 2. 3rd
from PyQt5.QtGui import QPainter, QFont, QPageLayout
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QAction, QGraphicsRectItem, \
    QGraphicsLineItem, QGraphicsSimpleTextItem, QGraphicsItem, QWidget, QStyleOptionGraphicsItem
# 3. local
from iosc.core import mycomtrade
from iosc.sig.pdfout.bar import SignalBarPrnItem

# x. const
A4 = (748, 1130)  # (w, h) of A4 - 10mm margins in "dots" (0.01")
H_ASIG = (176, 112)  # H of analog signal
H_SCALE = 20
W_COL0 = 112  # W of 1st column
X_COL0 = 5  # X-offset of signal label
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


class SignalPlotItem(QGraphicsItem):

    def __init__(self, parent='SignalItem'):
        super().__init__(parent)
        QGraphicsLineItem(0, 0, parent.w - W_COL0, parent.h, self)  # stub

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub


class SignalItem(QGraphicsItem):
    w: float
    h: float
    __signal: mycomtrade.Signal
    __plot: SignalPlotItem

    def __init__(self, w: int, h: int, signal: mycomtrade.Signal, parent=None):
        super().__init__(parent)
        self.w = w
        self.h = h
        self.__signal = signal
        # 1. name
        label = QGraphicsSimpleTextItem(signal.sid, self)
        label.setPos(5, h/2)
        # 2. plot
        self.__plot = SignalPlotItem(self)
        self.__plot.setPos(W_COL0, 0)
        # 3. underscore
        QGraphicsLineItem(0, h, w, h, self)

    def boundingRect(self) -> QRectF:
        return self.childrenBoundingRect()  # H == plot height, W = underscore

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        ...  # stub


class PrintRender(QGraphicsView):  # TODO: just scene container; can be replaced with QObject
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
        :param printer: Where to draw to
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
        for bar in self.parent().analog_table.bars[:1]:  # TODO: a) signal.height = h, b) h = signal.height()
            if not bar.hidden:
                item = SignalBarPrnItem(bar, False)  # FIXME: hidden
                item.setPos(0, y)
                self.scene().addItem(item)
                y += item.boundingRect().height()
                self.scene().addItem(QGraphicsLineItem(0, y, item.boundingRect().width(), y))
                y += 1
                # self.scene().addItem(s := SignalItem(w_all, H_ASIG[0], signal))
                # s.setPos(0, y)
                # y += H_ASIG[0]
        # output
        print(self.scene().itemsBoundingRect().height())  # 670.5
        self.scene().setSceneRect(self.scene().itemsBoundingRect())
        # self.render(QPainter(printer))  # Plan A. Sizes: dst: printer.pageSize(), src: self.viewport().rect()
        painter = QPainter(printer)
        self.scene().render(painter)  # Sizes: dst: printer.pageSize(), src: self.scene().sceneRect()
        printer.newPage()
        self.scene().render(painter)

"""
1 dot = .1"
"""
# 2. 3rd
from PyQt5.QtGui import QPainter, QFont, QPageLayout
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QAction, QGraphicsTextItem, QGraphicsRectItem, \
    QGraphicsLineItem
# 3. local
from iosc.core import mycomtrade
# x. const
A4 = (748, 1130)  # (w, h) of A4 - 10mm margins in "dots" (0.01")
H_ASIG = (176, 112)  # H of analog signal
H_SCALE = 20
W_COL0 = 112  # W of 1st column
MAIN_FONT = QFont('Source Code Pro', 8)  # 14x6 "dots"


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
        # TODO: while(signals) plot | pagebreak
        """
        # xsb = self.parent().xscroll_bar
        # print(xsb.norm_min, xsb.norm_max)
        if printer.pageLayout().orientation() == QPageLayout.Portrait:
            w_all, h_all = A4[0], A4[1]
        else:
            w_all, h_all = A4[1], A4[0]
        # fill
        self.scene().addItem(h := self.__mk_header())
        y = round(h.boundingRect().height())
        self.scene().addItem(t := self.__mk_table(w_all, h_all - y))
        t.setPos(0, y)
        # self.__mk_signals (for...)
        # output (TODO: scale, page break)
        print(self.scene().itemsBoundingRect().height())  # 670.5
        # self.render(QPainter(printer))  # Plan A. Sizes: dst: printer.pageSize(), src: self.viewport().rect()
        self.scene().render(QPainter(printer))  # Sizes: dst: printer.pageSize(), src: self.scene().sceneRect()

    def __mk_header(self) -> QGraphicsTextItem:
        # H: 50 (76 adjusted); independent on out format, page size
        # Draw from TL corner
        osc: mycomtrade.MyComtrade = self.parent().osc
        item = QGraphicsTextItem(  # 8
            f"{osc.path.name}"  # +14 = 22
            f"\nStart time: {osc.raw.start_timestamp.isoformat()}"  # +14 = 36
            f"\nDevice: {osc.raw.rec_dev_id}, Place: {osc.raw.station_name}"  # +14 = 50
        )
        item.setFont(MAIN_FONT)
        # item.adjustSize()  # wraps text
        return item

    def __mk_table(self, w: int, h: int) -> QGraphicsRectItem:
        # 1. border
        item = QGraphicsRectItem(0, 0, w, h - 0.5)
        # 2. columns separator
        QGraphicsLineItem(W_COL0, 0, W_COL0, h - 0.5, item)
        # 3. bottom strikeout
        QGraphicsLineItem(0, h - H_SCALE, w, h - H_SCALE, item)
        # 3. grid (= vlines + bottom digits)
        # TODO:
        # 4. _ptrs_
        return item

    def __test(self, y: float):
        ...

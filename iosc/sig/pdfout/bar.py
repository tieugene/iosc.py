"""SignalBar printing classes"""
# 1. std
# 2. 3rd
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsItemGroup
# 3. local
from iosc.sig.pdfout.ss import SignalSuitPrnLabelItem, SignalSuitPrnGraphItem

# x. const
H_BAR = 176  # bar height for A-signal, portrait
W_COL0 = 100


class SignalBarLabelPrnItem(QGraphicsItemGroup):
    # FIXME: shift, clip
    def __init__(self, bar: 'SignalBar', prn_value: bool, parent: 'SignalBarPrnItem' = None):
        super().__init__(parent)
        y = 0
        for ss in bar.signals:
            if not ss.hidden:
                item = SignalSuitPrnLabelItem(ss, prn_value)
                item.setPos(0, y)
                self.addToGroup(item)
                y += item.boundingRect().height()


class SignalBarPlotPrnItem(QGraphicsItemGroup):
    def __init__(self, bar: 'SignalBar', parent: 'SignalBarPrnItem' = None):
        super().__init__(parent)
        # FIXME: y=0 line
        for ss in bar.signals:
            if not ss.hidden:
                self.addToGroup(SignalSuitPrnGraphItem(ss))


class SignalBarPrnItem(QGraphicsItemGroup):
    """Object to print (labels + plot)"""
    __bar: 'SignalBar'
    __label: SignalBarLabelPrnItem
    __plot: SignalBarPlotPrnItem

    def __init__(self, bar: 'SignalBar', prn_value: bool, parent: QGraphicsItem = None):
        # TODO: add ref to render for options
        super().__init__(parent)
        self.__bar = bar
        self.__label = SignalBarLabelPrnItem(bar, prn_value)
        self.__plot = SignalBarPlotPrnItem(bar)
        self.__plot.setPos(W_COL0, 0)
        self.addToGroup(self.__label)
        self.addToGroup(self.__plot)

"""Graphics things (application dependent)."""
# 1. std
from typing import List
import math
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem, QApplication
# 3. local
from .const import W_LABEL, H_HEADER, H_BOTTOM
from .gitem import ThinPen, RectTextItem, ClipedPlainTextItem, GroupItem, TCPlainTextItem
from .bar import RowItem
from ..widget.sigbar import SignalBarList
from ...const import COLOR_PTR_MAIN, COLOR_PTR_OMP, COLOR_PTR_TMP, PENSTYLE_PTR_TMP

# x. const
PORS_TEXT = ('Primary', 'Secondary')


class HeaderItem(RectTextItem):
    """Page header."""

    __plot: 'PlotPrint'  # noqa: F821

    def __init__(self, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):  # noqa: F821
        """Init HeaderItem object."""
        info = oscwin.osc.info
        super().__init__(ClipedPlainTextItem(
            f"{oscwin.osc.path}" +
            QApplication.translate('HeaderItem', "\nStation ID: %s, Station name: %s") % (info['rec_dev_id'], info['station_name']) +
            QApplication.translate('HeaderItem', "\n%s values, Trigger time: %s") % (
                (
                    QApplication.translate('HeaderItem', "Primary"),
                    QApplication.translate('HeaderItem', "Secondary")
                )[int(oscwin.show_sec)],
                oscwin.osc.trigger_timestamp
            )
        ))
        self.__plot = plot
        self.update_size()

    def update_size(self):
        """Update geometry."""
        self.set_width(self.__plot.w_full)


class VItem(GroupItem):
    """Vertical line for TableCanvas."""

    _plot: 'PlotPrint'  # noqa: F821
    _line: QGraphicsLineItem
    _text: TCPlainTextItem

    def __init__(self, color: Qt.GlobalColor, plot: 'PlotPrint'):  # noqa: F821
        """Init VItem object.

        :param plot: Parent plot
        """
        super().__init__()
        self._plot = plot
        self._line = QGraphicsLineItem()
        self._line.setPen(ThinPen(color))
        self.addToGroup(self._line)


class TableCanvas(GroupItem):
    """Table frame.

    Contains:
    - header
    - border
    - columns separator
    - bottom underline
    - bottom scale
    - grid
    - ptrs (main, SC, tmp)
    """

    class GridItem(VItem):
        """Vertical grid line with bottom label."""

        __x: float
        __text: TCPlainTextItem

        def __init__(self, x: float, label: str, plot: 'PlotPrint'):  # noqa: F821
            """Init GridItem object.

            :param x: Normalized X-position, 0..1
            :param label: Text to label
            :param plot: Parent plot
            """
            super().__init__(Qt.GlobalColor.lightGray, plot)
            self.__x = x
            self.__text = TCPlainTextItem(label)
            self.addToGroup(self.__text)

        def update_size(self):
            """Update geometry."""
            x = W_LABEL + (self._plot.w_full - W_LABEL) * self.__x
            y = self._plot.h_full - H_BOTTOM
            self._line.setLine(x, H_HEADER, x, y)
            self.__text.setPos(x, y)

    class PtrItem(VItem):
        """Pointer representation."""

        __i: int

        def __init__(self, i: int, color: Qt.GlobalColor, plot: 'PlotPrint', pen_style: Qt.PenStyle = None):  # noqa: F821
            """Init PtrItem object.

            :param i: Xindex of pointer
            :param color: Subj
            :param plot: Parent plot
            :param pen_style: Subj
            """
            super().__init__(color, plot)
            self.__i = i
            if pen_style is not None:
                pen = self._line.pen()
                pen.setStyle(pen_style)
                self._line.setPen(pen)
            self.update_visibility()

        def update_size(self):
            """Update object geometry."""
            x = W_LABEL +\
                (self._plot.w_full - W_LABEL)\
                * (self.__i - self._plot.i_range[0])\
                / (self._plot.i_range[1] - self._plot.i_range[0])
            y = self._plot.h_full - H_BOTTOM
            self._line.setLine(x, H_HEADER, x, y)

        def update_visibility(self):
            """Show/hide pointer according to switcher."""
            self.setVisible(self._plot.prn_ptrs)

    __plot: 'PlotPrint'  # noqa: F821
    __header: HeaderItem
    __frame: QGraphicsRectItem  # external border; TODO: clip all inners (header, tic labels) by this
    __colsep: QGraphicsLineItem  # columns separator
    __btmsep: QGraphicsLineItem  # bottom separator
    __grid: List[GridItem]  # tics (v-line+label)
    __ptrs: List[PtrItem]  # pointers

    def __init__(self, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):  # noqa: F821
        """Init TableCanvas object."""
        super().__init__()
        self.__plot = plot
        self.__header = HeaderItem(oscwin, plot)
        pen = ThinPen(Qt.GlobalColor.gray)
        self.__frame = QGraphicsRectItem()
        self.__frame.setPen(pen)
        self.__frame.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape)
        self.__colsep = QGraphicsLineItem()
        self.__colsep.setPen(pen)
        self.__btmsep = QGraphicsLineItem()
        self.__btmsep.setPen(pen)
        self.__grid = list()
        self.__ptrs = list()
        # layout
        self.addToGroup(self.__header)
        self.addToGroup(self.__frame)
        self.addToGroup(self.__colsep)
        self.addToGroup(self.__btmsep)
        self.__mk_grid(oscwin)
        self.__mk_ptrs(oscwin)
        # go
        self.update_sizes()

    def __mk_grid(self, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Create grid items."""
        x_step: int = oscwin.x_px_width_us() * 100  # μs, grid step (1..1000 * 100, e.g. 1000)
        i_range = self.__plot.i_range
        t0: float = oscwin.osc.x[i_range[0]] * 1000  # μs, 1st sample position (e.g. -81666.(6))
        t1: float = oscwin.osc.x[i_range[1]] * 1000  # μs, last sample position (e.g. 116666.(6))
        t_size: float = t1 - t0
        x_us: int = math.ceil(t0 / x_step) * x_step  # μs, 1st grid position against xz
        # print(t0, t1, x_us, x_step)
        while x_us < t1:
            x_norm = (x_us - t0) / t_size
            num = str(x_us // 1000) if x_step > 1000 else "%.1f" % (x_us / 1000)
            self.__grid.append(self.GridItem(x_norm, num, self.__plot))
            self.__grid[-1].setParentItem(self.__frame)
            self.addToGroup(self.__grid[-1])
            x_us += x_step

    def __mk_ptrs(self, oscwin: 'ComtradeWidget'):  # noqa: F821
        """Create ponters (main, SC, tmp[])."""
        def __helper(__item):
            self.__ptrs.append(__item)
            self.__ptrs[-1].setParentItem(self.__frame)
            self.addToGroup(self.__ptrs[-1])
        i_range = self.__plot.i_range
        if i_range[0] <= (i := oscwin.main_ptr_i) <= i_range[1]:  # 1. MainPtr
            __helper(self.PtrItem(i, COLOR_PTR_MAIN, self.__plot))
        if oscwin.omp_ptr:
            if i_range[0] <= (i := oscwin.omp_ptr.i_sc) <= i_range[1]:  # 2. OMP ptrs
                __helper(self.PtrItem(i, COLOR_PTR_OMP, self.__plot))
            if i_range[0] <= (i := i - (oscwin.omp_ptr.w * oscwin.osc.spp)) <= i_range[1]:
                __helper(self.PtrItem(i, COLOR_PTR_OMP, self.__plot))
        for i in oscwin.tmp_ptr_i.values():  # 3. TmpPtr[]
            if i_range[0] <= i <= i_range[1]:
                __helper(self.PtrItem(i, COLOR_PTR_TMP, self.__plot, PENSTYLE_PTR_TMP))

    def update_sizes(self):
        """Update object sizes."""
        self.__header.update_size()
        self.__frame.setRect(0, H_HEADER, self.__plot.w_full, self.__plot.h_full - H_HEADER)
        self.__colsep.setLine(W_LABEL, H_HEADER, W_LABEL, self.__plot.h_full - H_BOTTOM)
        self.__btmsep.setLine(0, self.__plot.h_full - H_BOTTOM, self.__plot.w_full, self.__plot.h_full - H_BOTTOM)
        for g in self.__grid:
            g.update_size()
        for p in self.__ptrs:
            p.update_size()

    def update_ptrs_visibility(self):
        """Show/hide pointers."""
        for p in self.__ptrs:
            p.update_visibility()


class TablePayload(GroupItem):
    """Just rows with underlines.

    Used in: PlotScene > … > Print
    """

    __rowitem: list[RowItem]

    def __init__(self, sblist: SignalBarList, plot: 'PlotPrint'):  # noqa: F821
        """Init TablePayload object."""
        super().__init__()
        self.__rowitem = list()
        y = 0
        # return  # stub
        for sb in sblist:
            item = RowItem(sb, plot)
            item.setY(y)
            self.__rowitem.append(item)
            self.addToGroup(self.__rowitem[-1])
            y += item.boundingRect().height()

    def update_sizes(self):
        """Update object sizes on paint region changed."""
        # y = self.__rowitem[0].boundingRect().y()
        y = H_HEADER
        for item in self.__rowitem:
            item.update_size()
            item.setY(y)
            y += item.boundingRect().height()

    def update_ptrs_visibility(self):
        """Show/hide pointers according to switcher."""
        for item in self.__rowitem:
            item.update_ptrs_visibility()

    def update_labels(self):
        """Show/hide signal labels according to switcher."""
        for item in self.__rowitem:
            item.update_labels()


class PlotScene(QGraphicsScene):
    """Used in: PlotPrint > PrintView."""

    __canvas: TableCanvas
    __payload: TablePayload

    def __init__(self, sblist: SignalBarList, oscwin: 'ComtradeWidget', plot: 'PlotPrint'):  # noqa: F821
        """Init PlotScene."""
        super().__init__()
        self.__canvas = TableCanvas(oscwin, plot)
        self.__payload = TablePayload(sblist, plot)
        self.__payload.setY(H_HEADER)
        self.addItem(self.__canvas)
        self.addItem(self.__payload)

    def update_sizes(self):
        """Update object sizes on paint region changed."""
        self.__canvas.update_sizes()
        self.__payload.update_sizes()
        self.setSceneRect(self.itemsBoundingRect())

    def update_labels(self):
        """Show/hide signal labels according to switcher."""
        self.__payload.update_labels()

    def update_ptrs_visibility(self):
        """Show/hide pointers according to switcher."""
        self.__canvas.update_ptrs_visibility()
        self.__payload.update_ptrs_visibility()

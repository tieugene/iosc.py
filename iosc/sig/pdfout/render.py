# 1. std
from typing import List
# 2. 3rd
from PyQt5.QtGui import QPainter
from PyQt5.QtPrintSupport import QPrinter
# 3. local
from .const import PORTRAIT, W_PAGE, H_ROW_BASE, H_HEADER, H_BOTTOM
from .gitem import GraphViewBase
from .gsuit import PlotScene
from .pdfprinter import PdfPrinter
from iosc.sig.widget.common import SignalBarList, SignalBar


class PlotBase(GraphViewBase):
    """Used in: PlotView, PlotPrint"""
    _portrait: bool
    _prn_values: bool
    _scene: List[PlotScene]

    def __init__(self, bslist: SignalBarList):
        super().__init__()
        self._portrait = PORTRAIT
        self._prn_values = False
        self._scene = list()
        i0 = 0
        for k in self.__data_split(bslist):
            self._scene.append(PlotScene(bslist[i0:i0 + k], self))
            i0 += k

    @property
    def portrait(self) -> bool:
        return self._portrait

    @property
    def prn_values(self) -> bool:
        return self._prn_values

    @property
    def w_full(self) -> int:
        """Current full table width"""
        return W_PAGE[int(self.portrait)]

    @property
    def h_full(self) -> int:
        """Current full table width"""
        return W_PAGE[1 - int(self.portrait)]

    def h_row(self, sb: SignalBar) -> int:  # FIXME:
        """Row height as f(sb.is_bool, sb.h[default], self.portrait).
        - if is_bool: exact H_ROW_BASE
        - else: defined or 4 × H_ROW_BASE
        - finally × 1.5 if portrait
        :todo: cache it
        """
        lp_mult = 1.5 if self.portrait else 1  # multiplier for landscape/portrait
        h_base = H_ROW_BASE if sb.is_bool else sb.height or H_ROW_BASE * 4  # 28/112, 42/168
        return round(h_base * lp_mult)

    @property
    def scene_count(self) -> int:
        return len(self._scene)

    def slot_set_portrait(self, v: bool):
        if self._portrait ^ v:
            self._portrait = v
            for scene in self._scene:
                scene.update_sizes()
            # self.slot_reset_size()  # optional

    def _slot_set_prn_values(self, v: bool):
        if self._prn_values ^ v:
            self._prn_values = v
            for scene in self._scene:
                scene.update_labels()

    def __data_split(self, __sblist: SignalBarList) -> List[int]:
        """Split data to scene pieces.
        :return: list of bar numbers
        """
        retvalue = list()
        h_barlist_max = W_PAGE[1] - H_HEADER - H_BOTTOM  # max v-space for bars
        cur_num = cur_height = 0  # heigth of current piece in basic (B) units
        for i, bs in enumerate(__sblist):
            h = self.h_row(bs)
            if cur_height + h > h_barlist_max:  # analog?
                retvalue.append(cur_num)
                cur_num = cur_height = 0
            cur_num += 1
            cur_height += h
        retvalue.append(cur_num)
        return retvalue


class PlotPrint(PlotBase):
    """
    :todo: just scene container; can be replaced with QObject?
    """
    def __init__(self, sblist: SignalBarList):
        super().__init__(sblist)

    def slot_paint_request(self, printer: PdfPrinter):
        """
        Call _B4_ show dialog
        Use printer.pageRect(QPrinter.Millimeter/DevicePixel).
        :param printer: Where to draw to
        """
        self.slot_set_portrait(printer.orientation() == QPrinter.Orientation.Portrait)
        self._slot_set_prn_values(printer.option_2lines)
        painter = QPainter(printer)
        self._scene[0].render(painter)  # Sizes: dst: printer.pageSize(), src: self.scene().sceneRect()
        for scene in self._scene[1:]:
            printer.newPage()
            scene.render(painter)
        painter.end()

"""Signal tab widget.

RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import json
import pathlib
from typing import Any, Dict, Optional, List
# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QCloseEvent, QHideEvent, QShowEvent, QColor, QRgba64
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMenuBar, QToolBar, QAction, QMessageBox, QFileDialog, \
    QHBoxLayout, QActionGroup, QToolButton, QMenu
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.core.tocsv import export_to_csv
from iosc.icon import svg_icon, ESvgSrc
from iosc.core.convtrade import convert, ConvertError
from iosc.sig.calc.dialog import MathModuleDialog
from iosc.sig.pdfout.dialog import PDFOutPreviewDialog
from iosc.sig.pdfout.pdfprinter import PdfPrinter
from iosc.sig.tools.cvdwindow import CVDWindow
from iosc.sig.tools.hdwindow import HDWindow
from iosc.sig.tools.ompmap import OMPMapWindow
from iosc.sig.tools.vtwindow import VTWindow
from iosc.sig.widget.finder import FindDialog
from iosc.sig.widget.section import SignalBarTable
from iosc.sig.widget.bottom import TimeStampsBar, XScroller
from iosc.sig.widget.top import TimeAxisBar
from iosc.sig.widget.sigsuit import StatusSignalSuit, AnalogSignalSuit, ABSignalSuit
from iosc.sig.widget.dialog import TmpPtrDialog, SelectSignalsDialog


class OMPPtr:
    """OMP pointers."""
    __osc: mycomtrade.MyComtrade
    __i0: int  # t=0
    i_sc: int  # SC pointer position, sample no; former __sc_ptr_i, sc_ptr_i
    w: int  # width, periods; former __omp_width omp_width
    w_max: int  # pre-calculated (on load) max wwidth
    # depend
    i_sc_min: int  # precalculated min i, depends on PR<=w; = max(T, )
    i_sc_max: int  # precalcultaed max i, depends on PR<=w; = min(tmax, )

    def __init__(self, osc: mycomtrade.MyComtrade, i0: int):
        self.__osc = osc
        self.__i0 = i0
        self.i_sc = i0 + self.__osc.spp
        self.w = 2
        self.w_max = min((self.__osc.total_samples - 1) // self.__osc.spp, 10)
        self.__upd_i_sc_limits()

    @property
    def i_pr(self) -> int:  # former pr_ptr_i
        return self.i_sc - self.__osc.spp * self.w

    def set_w(self, w_new: int):
        """Update PR-SC distance."""
        if w_new == self.w:
            return
        self.i_sc += (w_new - self.w) * self.__osc.spp
        if w_new > self.w:
            if self.i_sc > self.__osc.total_samples - 1:
                self.i_sc = self.__osc.total_samples - 1
        else:
            if self.i_sc < self.__i0 + self.__osc.spp:
                self.i_sc = self.__i0 + self.__osc.spp
        self.w = w_new
        self.__upd_i_sc_limits()

    def __upd_i_sc_limits(self):
        self.i_sc_min = max(self.__i0 + self.__osc.spp, self.__osc.spp * self.w)
        self.i_sc_max = min(self.__osc.total_samples - 1, self.__i0 + self.__osc.spp * self.w - 1)


class ComtradeWidget(QWidget):
    """Main osc window."""

    # inner vars
    __father: 'ComtradeTabWidget'  # noqa: F821; real parent
    osc: mycomtrade.MyComtrade
    col_ctrl_width: int
    # inner vars
    __main_ptr_i: int  # current Main Ptr index in source arrays
    omp_ptr: Optional[OMPPtr]
    __tmp_ptr_i: dict[int, int]  # current Tmp Ptr indexes in source arrays: ptr_uid => x_idx
    msr_ptr_uids: set[int]  # MsrPtr uids
    lvl_ptr_uids: set[int]  # LvlPtr uids
    __shifted: bool  # original/shifted selector
    x_zoom: int
    show_sec: bool  # pri/sec selector
    viewas: int  # TODO: enum
    ass_list: List[AnalogSignalSuit]  # Translate signal no to chart widget
    # actions
    action_close: QAction
    action_info: QAction
    action_convert: QAction
    action_pdfout: QAction
    action_csv: QAction
    action_cfg_save: QAction
    action_cfg_load: QAction
    action_resize_y_in: QAction
    action_resize_y_out: QAction
    action_zoom_x_in: QAction
    action_zoom_x_out: QAction
    action_unhide: QAction
    action_centered: QAction
    action_pors: QActionGroup
    action_pors_pri: QAction
    action_pors_sec: QAction
    action_viewas: QActionGroup
    action_viewas_is: QAction
    action_viewas_mid: QAction
    action_viewas_eff: QAction
    action_viewas_hrm1: QAction
    action_viewas_hrm2: QAction
    action_viewas_hrm3: QAction
    action_viewas_hrm5: QAction
    action_ptr_add_tmp: QAction
    action_ptr_add_msr: QAction
    action_ptr_add_lvl: QAction
    action_mainptr_l: QAction
    action_mainptr_r: QAction
    action_vector_diagram: QAction
    action_harmonic_diagram: QAction
    action_value_table: QAction
    action_omp_map: QAction
    action_omp_save: QAction
    action_signal_find: QAction
    action_math_module: QAction
    # widgets
    menubar: QMenuBar
    toolbar: QToolBar
    viewas_toolbutton: QToolButton
    timeaxis_bar: TimeAxisBar
    analog_table: SignalBarTable
    status_table: SignalBarTable
    timestamps_bar: TimeStampsBar
    xscroll_bar: XScroller
    cvdwin: Optional[CVDWindow]  # TODO: List[CVDWindow]
    hdwin: Optional[HDWindow]  # TODO: List[HDWindow]
    ompmapwin: Optional[OMPMapWindow]
    __printer: PdfPrinter
    __print_preview: PDFOutPreviewDialog
    # signals
    signal_chged_pors = pyqtSignal()  # recalc ASignalCtrlView on ...
    signal_chged_shift = pyqtSignal()  # refresh ASignal*View on switching original/shifted
    signal_chged_func = pyqtSignal()  # refresh ASignal*View on switching function
    signal_resize_col_ctrl = pyqtSignal(int)
    signal_unhide_all = pyqtSignal()
    signal_x_zoom = pyqtSignal()
    signal_ptr_moved_main = pyqtSignal(int)  # refresh Signal(Ctrl/Chart)View on MainPtr moved
    signal_ptr_moved_sc = pyqtSignal(int)  # refresh SignalChartWidget on OMP SC Ptr moved
    signal_ptr_moved_pr = pyqtSignal(int)  # refresh SignalChartWidget on OMP PR Ptr moved
    signal_ptr_add_tmp = pyqtSignal(int)  # add new TmpPtr in each SignalChartWidget
    signal_ptr_del_tmp = pyqtSignal(int)  # rm TmpPtr from each SignalChartWidget
    signal_ptr_moved_tmp = pyqtSignal(int, int)  # refresh SignalChartWidget on Tmp Ptr moved

    def __init__(self, osc: mycomtrade.MyComtrade, parent: 'ComtradeTabWidget'):  # noqa: F821
        """Init ComtradeWidget object."""
        super().__init__(parent)
        self.__father = parent
        self.osc = osc
        self.col_ctrl_width = iosc.const.COL0_WIDTH_INIT
        self.__main_ptr_i = self.x2i(0.0)  # default: Z (Osc1: 600)
        if osc.bad_gap_l() or osc.bad_gap_r():
            self.omp_ptr = None
        else:
            self.omp_ptr = OMPPtr(osc, self.__main_ptr_i)
        self.__tmp_ptr_i = {}
        self.msr_ptr_uids = set()
        self.lvl_ptr_uids = set()
        self.__shifted = False
        self.x_zoom = len(iosc.const.X_PX_WIDTH_uS) - 1  # initial: max
        self.show_sec = True
        self.viewas = 0
        self.ass_list = []
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_toolbar()
        self.__set_data()
        self.__update_xzoom_actions()
        self.__mk_connections()
        if not self.omp_ptr:
            QMessageBox.warning(
                self,
                self.tr("OMP error"),
                self.tr("Unable to set OMP pointers: too few osc width.")
            )

    def x_px_width_us(self) -> int:
        """:return: Current px width, μs."""
        return iosc.const.X_PX_WIDTH_uS[self.x_zoom]

    # property
    def x_width_px(self) -> int:
        """:return: Current graph width, px."""
        return round(self.osc.x_size * 1000 / self.x_px_width_us())

    # property
    def x_sample_width_px(self) -> int:
        """:return: Current width of samples interval, px."""
        return round(self.x_width_px() / self.osc.total_samples)

    @property
    def main_ptr_i(self) -> int:
        """:return: Sample number of main pointer."""
        return self.__main_ptr_i

    @property
    def tmp_ptr_i(self) -> Dict[int, int]:
        """Requisitions of tmp pointers."""
        return self.__tmp_ptr_i

    @property
    def shifted(self):
        """:return: Whether osc signals are shifted.

        :fixme: rm?
        :todo: mv to 'centered'
        """
        return self.osc.shifted

    def x2i(self, x: float) -> int:
        """Sample number of time (ms)."""
        return int(round((x - self.osc.x_min) / 1000 * self.osc.rate))

    def i2x(self, i: int) -> float:
        """Time of Sample number (ms)."""
        return self.osc.x[i]

    def __mk_widgets(self):
        """Make child widgets."""
        self.menubar = QMenuBar()
        self.toolbar = QToolBar(self)
        self.viewas_toolbutton = QToolButton(self)
        self.timeaxis_bar = TimeAxisBar(self)
        self.analog_table = SignalBarTable(self)
        self.status_table = SignalBarTable(self)
        self.timestamps_bar = TimeStampsBar(self)
        self.xscroll_bar = XScroller(self)
        self.cvdwin = None
        self.hdwin = None
        self.ompmapwin = None
        self.__printer = PdfPrinter()
        self.__print_preview = PDFOutPreviewDialog(self.__printer, self)

    def __mk_layout(self):
        """Lay out child widgets."""
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        # 1. top
        topbar = QWidget()
        topbar.setLayout(QHBoxLayout())
        topbar.layout().setContentsMargins(0, 0, 0, 0)
        topbar.layout().setSpacing(0)
        topbar.layout().addWidget(self.menubar)
        topbar.layout().addWidget(self.toolbar)
        self.layout().addWidget(topbar)
        # 2. timeline
        self.layout().addWidget(self.timeaxis_bar)
        # 3. 2 x signal tables
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.analog_table)
        splitter.addWidget(self.status_table)
        self.layout().addWidget(splitter)
        # 4. bottom status bar
        self.layout().addWidget(self.timestamps_bar)
        # 5. bottom scrollbar
        self.layout().addWidget(self.xscroll_bar)

    def __mk_actions(self):
        """Make required actions."""
        # noinspection PyArgumentList
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    self.tr("&Close"),
                                    self,
                                    shortcut="Ctrl+W",
                                    triggered=self.__do_file_close)
        # noinspection PyArgumentList
        self.action_info = QAction(QIcon.fromTheme("dialog-information"),
                                   self.tr("&Info"),
                                   self,
                                   shortcut="Ctrl+I",
                                   triggered=self.__do_file_info)
        # noinspection PyArgumentList
        self.action_convert = QAction(QIcon.fromTheme("document-save-as"),
                                      self.tr("&Save as..."),
                                      self,
                                      triggered=self.__do_file_convert)
        # noinspection PyArgumentList
        self.action_csv = QAction(self.tr("&Export to CSV"),
                                  self,
                                  triggered=self.__do_file_csv)
        # noinspection PyArgumentList
        self.action_cfg_save = QAction(QIcon.fromTheme("document-save"),
                                       self.tr("&Save settings"),
                                       self,
                                       shortcut="Ctrl+S",
                                       triggered=self.__do_cfg_save)
        # noinspection PyArgumentList
        self.action_cfg_load = QAction(QIcon.fromTheme("document-open"),
                                       self.tr("&Load settings"),
                                       self,
                                       shortcut="Ctrl+L",
                                       triggered=self.__do_cfg_load)
        # noinspection PyArgumentList
        self.action_pdfout = QAction(svg_icon(ESvgSrc.PDF),
                                     self.tr("&Print..."),
                                     self,
                                     shortcut="Ctrl+P",
                                     triggered=self.__print_preview.open)
        # noinspection PyArgumentList
        self.action_resize_y_in = QAction(svg_icon(ESvgSrc.VZoomIn),
                                          self.tr("Y-Resize +"),
                                          self,
                                          triggered=self.__do_resize_y_all_inc)
        # noinspection PyArgumentList
        self.action_resize_y_out = QAction(svg_icon(ESvgSrc.VZoomOut),
                                           self.tr("Y-Resize -"),
                                           self,
                                           triggered=self.__do_resize_y_all_dec)
        # noinspection PyArgumentList
        self.action_zoom_x_in = QAction(svg_icon(ESvgSrc.HZoomIn),
                                        self.tr("X-Zoom in"),
                                        self,
                                        triggered=self.__do_xzoom_in)
        # noinspection PyArgumentList
        self.action_zoom_x_out = QAction(svg_icon(ESvgSrc.HZoomOut),
                                         self.tr("X-Zoom out"),
                                         self,
                                         triggered=self.__do_xzoom_out)
        # noinspection PyArgumentList
        self.action_centered = QAction(svg_icon(ESvgSrc.ShiftCentered),
                                       self.tr("&Centered"),
                                       self,
                                       checkable=True,
                                       triggered=self.__do_centered
                                       )
        # noinspection PyArgumentList
        self.action_pors_pri = QAction(svg_icon(ESvgSrc.PorsP),
                                       self.tr("&Primary"),
                                       self,
                                       checkable=True)
        # noinspection PyArgumentList
        self.action_pors_sec = QAction(svg_icon(ESvgSrc.PorsS),
                                       self.tr("&Secondary"),
                                       self,
                                       checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_is = QAction(self.tr("As &is"),
                                        self,
                                        checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_mid = QAction(self.tr("&Mid."),
                                         self,
                                         checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_eff = QAction(self.tr("&Eff."),
                                         self,
                                         checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_hrm1 = QAction(self.tr("Hrm. &1"),
                                          self,
                                          checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_hrm2 = QAction(self.tr("Hrm. &2"),
                                          self,
                                          checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_hrm3 = QAction(self.tr("Hrm. &3"),
                                          self,
                                          checkable=True)
        # noinspection PyArgumentList
        self.action_viewas_hrm5 = QAction(self.tr("Hrm. &5"),
                                          self,
                                          checkable=True)
        # noinspection PyArgumentList
        self.action_unhide = QAction(QIcon.fromTheme("edit-undo"),
                                     self.tr("&Unhide all"),
                                     self,
                                     triggered=self.__do_signal_unhide)
        # noinspection PyArgumentList
        self.action_signal_find = QAction(self.tr("Find..."),
                                          self,
                                          shortcut="Ctrl+F",
                                          triggered=self.__do_signal_find)
        # noinspection PyArgumentList
        self.action_math_module = QAction(self.tr("Module"),
                                          self,
                                          triggered=self.__do_math_module)
        # noinspection PyArgumentList
        self.action_ptr_add_tmp = QAction(self.tr("Add temporary pointer"),
                                          self,
                                          triggered=self.__do_ptr_add_tmp)
        # noinspection PyArgumentList
        self.action_ptr_add_msr = QAction(self.tr("Add measure pointers"),
                                          self,
                                          triggered=self.__do_ptr_add_msr)
        # noinspection PyArgumentList
        self.action_ptr_add_lvl = QAction(self.tr("Add level pointers"),
                                          self,
                                          triggered=self.__do_ptr_add_lvl)
        # noinspection PyArgumentList
        self.action_mainptr_l = QAction(self.tr("Move main pointer left"),
                                        self,
                                        shortcut="Left",
                                        triggered=self.__do_mainptr_l)
        # noinspection PyArgumentList
        self.action_mainptr_r = QAction(self.tr("Move main pointer right"),
                                        self,
                                        shortcut="Right",
                                        triggered=self.__do_mainptr_r)
        # noinspection PyArgumentList
        self.action_vector_diagram = QAction(self.tr("Vector chart"),
                                             self,
                                             shortcut="Ctrl+V",
                                             triggered=self.__do_vector_diagram)
        # noinspection PyArgumentList
        self.action_harmonic_diagram = QAction(self.tr("Harmonic chart"),
                                               self,
                                               shortcut="Ctrl+H",
                                               triggered=self.__do_harmonic_diagram)
        # noinspection PyArgumentList
        self.action_value_table = QAction(QIcon.fromTheme("x-office-spreadsheet"),
                                          self.tr("Value table"),
                                          self,
                                          shortcut="Ctrl+T",
                                          triggered=self.__do_value_table)
        # noinspection PyArgumentList
        self.action_omp_map = QAction(self.tr("OMP map table"),
                                      self,
                                      shortcut="Ctrl+M",
                                      triggered=self.__do_omp_map)
        # noinspection PyArgumentList
        self.action_omp_save = QAction(self.tr("OMP map save"),
                                       self,
                                       triggered=self.__do_omp_save)
        self.action_pors = QActionGroup(self)
        self.action_pors.addAction(self.action_pors_pri)
        self.action_pors.addAction(self.action_pors_sec).setChecked(True)
        self.action_viewas = QActionGroup(self)
        self.action_viewas.addAction(self.action_viewas_is).setData(0)
        self.action_viewas.addAction(self.action_viewas_mid).setData(1)
        self.action_viewas.addAction(self.action_viewas_eff).setData(2)
        self.action_viewas.addAction(self.action_viewas_hrm1).setData(3)
        self.action_viewas.addAction(self.action_viewas_hrm2).setData(4)
        self.action_viewas.addAction(self.action_viewas_hrm3).setData(5)
        self.action_viewas.addAction(self.action_viewas_hrm5).setData(6)
        self.action_viewas_is.setChecked(True)
        self.action_zoom_x_out.setEnabled(False)
        # specials
        self.action_omp_map.setEnabled(bool(self.omp_ptr))
        self.action_omp_save.setEnabled(bool(self.omp_ptr))

    def __mk_menu(self):
        """Make local (osc) menu."""
        self.menubar.addMenu(self.tr("&File")).addActions((
            self.action_info,
            self.action_convert,
            self.action_csv,
            self.action_cfg_save,
            self.action_cfg_load,
            self.action_pdfout,
            self.action_close
        ))
        menu_view = self.menubar.addMenu(self.tr("&View"))
        menu_view.addActions((
            self.action_resize_y_in,
            self.action_resize_y_out,
            self.action_zoom_x_in,
            self.action_zoom_x_out,
            self.action_centered
        ))
        menu_view.addMenu(self.tr("P/S")).addActions((
            self.action_pors_pri,
            self.action_pors_sec
        ))
        menu_view.addMenu(self.tr("View as...")).addActions((
            self.action_viewas_is,
            self.action_viewas_mid,
            self.action_viewas_eff,
            self.action_viewas_hrm1,
            self.action_viewas_hrm2,
            self.action_viewas_hrm3,
            self.action_viewas_hrm5
        ))
        menu_signal = self.menubar.addMenu(self.tr("&Signal"))
        menu_signal.addActions((
            self.action_unhide,
            self.action_signal_find
        ))
        # menu_signal.addMenu(self.tr("Maths")).addMenu(self.tr("Conversions")).addAction(self.action_math_module)
        self.menubar.addMenu(self.tr("&Pointers")).addActions((
            self.action_ptr_add_tmp,
            self.action_ptr_add_msr,
            self.action_ptr_add_lvl,
            self.action_mainptr_l,
            self.action_mainptr_r
        ))
        self.menubar.addMenu(self.tr("&Tools")).addActions((
            self.action_vector_diagram,
            self.action_harmonic_diagram,
            self.action_value_table,
            self.action_omp_map,
            self.action_omp_save
        ))

    def __mk_toolbar(self):
        """Make local (osc) toolbar."""
        # prepare
        self.viewas_toolbutton.setPopupMode(QToolButton.MenuButtonPopup)
        viewas_menu = QMenu()
        viewas_menu.addActions(self.action_viewas.actions())
        self.viewas_toolbutton.setMenu(viewas_menu)
        self.viewas_toolbutton.setDefaultAction(self.action_viewas.actions()[self.viewas])
        # go
        self.toolbar.addAction(self.action_resize_y_in)
        self.toolbar.addAction(self.action_resize_y_out)
        self.toolbar.addAction(self.action_zoom_x_in)
        self.toolbar.addAction(self.action_zoom_x_out)
        self.toolbar.addAction(self.action_centered)
        self.toolbar.addAction(self.action_pors_pri)
        self.toolbar.addAction(self.action_pors_sec)
        self.toolbar.addWidget(self.viewas_toolbutton)
        self.toolbar.addAction(self.action_info)

    def __mk_connections(self):
        """Link required signals/slots."""
        self.action_pors.triggered.connect(self.__do_pors)
        self.action_viewas.triggered.connect(self.__do_viewas)
        self.xscroll_bar.valueChanged.connect(self.timeaxis_bar.plot.slot_rerange_force)
        self.xscroll_bar.valueChanged.connect(self.timestamps_bar.plot.slot_rerange_force)
        self.xscroll_bar.signal_update_plots.connect(self.timeaxis_bar.plot.slot_rerange)
        self.xscroll_bar.signal_update_plots.connect(self.timestamps_bar.plot.slot_rerange)

    def __set_data(self):
        """Fill out signal tables 1st time."""
        for sig in self.osc.y:
            if not sig.is_bool:
                self.analog_table.bar_insert().sig_add(ass := AnalogSignalSuit(sig, self))  # FIXME: default height
                self.ass_list.append(ass)
            else:
                self.status_table.bar_insert().sig_add(StatusSignalSuit(sig, self))  # FIXME: default height

    def __ofg_store(self) -> dict:
        """Collect osc settings to save.

        :todo: capsulate
        """
        data = {
            'ver': iosc.const.OFG_VER,
            'xzoom': self.x_zoom,
            'mode': {
                'pors': self.show_sec,
                'viewas': self.viewas,
                'shift': self.__shifted,
            },
            'ptr': {
                'main': self.__main_ptr_i
            },
            'table': []
        }
        if self.omp_ptr:
            data['ptr']['omp'] = {'xi': self.omp_ptr.i_sc, 'w': self.omp_ptr.w}
        if self.__tmp_ptr_i:
            tmp = []
            for uid, i in self.__tmp_ptr_i.items():
                tmp.append({'uid': uid, 'xi': i})
            data['ptr']['tmp'] = tmp
        # bars
        for table in (self.analog_table, self.status_table):
            t_data = []
            for bar in table.bars:
                b_data = {'s': []}
                if not bar.is_bool():
                    b_data['h'] = bar.height
                    b_data['yzoom'] = bar.zoom_y
                for ss in bar.signals:
                    s_data = {
                        'i': ss.i,
                        # 'num': ss.num,  # FIXME: ×?
                        'show': not ss.hidden,
                        'color': int(ss.color.rgba64()),
                    }
                    if not ss.is_bool:
                        s_data['style'] = ss.line_style
                        if ss.msr_ptr:
                            ptrs = []
                            for uid, v in ss.msr_ptr.items():
                                ptrs.append({'uid': uid, 'xi': v[0].i, 'f': v[2]})
                            s_data['ptr_msr'] = ptrs
                        if ss.lvl_ptr:
                            ptrs = []
                            for uid, v in ss.lvl_ptr.items():
                                ptrs.append({'uid': uid, 'y': v[0].get_y_rel()})
                            s_data['ptr_lvl'] = ptrs
                    b_data['s'].append(s_data)
                t_data.append(b_data)
            data['table'].append(t_data)
        # tools
        tool = {}
        # - CDV
        if self.cvdwin:
            tool['cvd'] = {
                'show': self.cvdwin.isVisible(),
                'base': self.cvdwin.ss_base.i,
                'used': [ss.i for ss in self.cvdwin.ss_used]
            }
        # - HD
        if self.hdwin:
            tool['hd'] = {
                'show': self.hdwin.isVisible(),
                'used': [ss.i for ss in self.hdwin.ss_used]
            }
        # - OMP
        if self.ompmapwin:
            tool['omp'] = {
                'show': self.ompmapwin.isVisible(),
                'used': self.ompmapwin.ofd_to()
            }
        if tool:
            data['tool'] = tool
        return data

    def __ofg_restore(self, data: dict):
        """Restore osc from *.ofg content.

        :todo: capsulate
        """
        if data['ver'] != iosc.const.OFG_VER:
            QMessageBox.critical(
                self,
                self.tr("OFG loading error"),
                self.tr("Incompatible version: %s") % data['ver']
            )
        # 1. clean
        # 1.1. Tmp ptrs
        for uid in self.__tmp_ptr_i:  # .keys()
            self.slot_ptr_del_tmp(uid)
        # 1.2. store SS' | detch them | drop bars
        sss: List[Optional[ABSignalSuit]] = [None] * len(self.osc.y)
        for table in (self.analog_table, self.status_table):
            for bar in table.bars[::-1]:  # reverse order
                for ss in bar.signals:
                    sss[ss.i] = ss
                    if not ss.is_bool:
                        for uid in tuple(ss.msr_ptr.keys()):  # fix dynamic
                            ss.del_ptr_msr(uid)
                        for uid in tuple(ss.lvl_ptr.keys()):  # fix dynamic
                            ss.del_ptr_lvl(uid)
                    ss.detach()
                bar.suicide()
        # 2. Restore
        # 2.1. mk bars | add SS'
        for ti, table in enumerate((self.analog_table, self.status_table)):
            src_table = data['table'][ti]
            for src_bar in src_table:
                dst_bar = table.bar_insert()
                for src_ss in src_bar['s']:
                    ss = sss[src_ss['i']]
                    dst_bar.sig_add(ss)
                    ss.hidden = not src_ss['show']  # show
                    ss.color = QColor.fromRgba64(QRgba64.fromRgba64(src_ss['color']))  # color
                    if not ss.is_bool:
                        ss.line_style = src_ss['style']  # style
                        for ptr in src_ss.get('ptr_msr', []):  # MsrPtr
                            ss.add_ptr_msr(ptr['uid'], ptr['xi'], ptr['f'])
                        for ptr in src_ss.get('ptr_lvl', []):  # LvlPtr
                            ss.add_ptr_lvl(ptr['uid'], ptr['y'])
                if not dst_bar.is_bool():
                    dst_bar.height = src_bar['h']  # height
                    dst_bar.zoom_y = src_bar['yzoom']  # yzoom
        # 2.1. Window
        self.__update_xzoom(data['xzoom'])  # - x-zoom
        # - modes
        # -- shift
        if data['mode']['shift']:
            self.action_centered.setChecked(True)
        # -- pors
        if data['mode']['pors']:
            self.action_pors_sec.setChecked(True)
        else:
            self.action_pors_pri.setChecked(True)
        # -- viewas
        act = self.action_viewas.actions()[data['mode']['viewas']]
        act.setChecked(True)
        self.__do_viewas(act)
        # 2.2. Ptrs
        # - MainPtr
        self.slot_ptr_moved_main(data['ptr']['main'])
        # - SC ptrs
        if self.omp_ptr:
            self.omp_ptr.w = data['ptr']['omp']['w']  # hack but...
            self.slot_ptr_moved_sc(data['ptr']['omp']['xi'])
        # - Tmp ptrs
        for ptr in data['ptr'].get('tmp', []):
            self.__ptr_add_tmp(ptr['uid'], ptr['xi'])
        # 2.3. Tools
        if 'tool' in data:
            # - CVD
            if src := data['tool'].get('cvd'):
                if not self.cvdwin:
                    self.cvdwin = CVDWindow(self)
                self.cvdwin.ss_used.clear()
                for i in src['used']:
                    self.cvdwin.ss_used.append(self.ass_list[i])
                self.cvdwin.ss_base = self.ass_list[src['base']]
                self.cvdwin.chart.reload_signals()
                self.cvdwin.table.reload_signals()
                if src['show']:
                    self.__do_vector_diagram()
                # FIXME: signals visibility
            # - HD
            if src := data['tool'].get('hd'):
                if not self.hdwin:
                    self.hdwin = HDWindow(self)
                self.hdwin.ss_used.clear()
                for i in src['used']:
                    self.hdwin.ss_used.append(self.ass_list[i])
                self.hdwin.table.reload_signals()
                if src['show']:
                    self.__do_harmonic_diagram()
            # - OMP map
            if src := data['tool'].get('omp'):
                if not self.ompmapwin:
                    self.ompmapwin = OMPMapWindow(self)
                self.ompmapwin.ofd_from(src['used'])
                self.ompmapwin.exec_1 = False
                if src['show']:
                    self.__do_omp_map()

    def __update_xzoom_actions(self):
        """Set X-zoom actions availability."""
        self.action_zoom_x_in.setEnabled(self.x_zoom > 0)
        self.action_zoom_x_out.setEnabled(self.x_zoom < (len(iosc.const.X_PX_WIDTH_uS) - 1))

    def __update_xzoom(self, xz: int):
        """Change X-zoom.

        :param xz: New X-zoom value
        :todo: add force:bool=False
        """
        if (xz != self.x_zoom) and (0 <= xz < len(iosc.const.X_PX_WIDTH_uS)):
            self.x_zoom = xz
            self.__update_xzoom_actions()
            self.signal_x_zoom.emit()
            self.timeaxis_bar.plot.signal_width_changed.emit(self.timeaxis_bar.plot.viewport().width())  # FIXME: hack

    def __ptr_add_tmp(self, uid: int, i: int):
        """Add new tmp pointer.

        :param uid: Pinter uniq id.
        :param i: Sample number.
        :todo: optional name:str
        """
        self.__tmp_ptr_i[uid] = i
        self.signal_ptr_add_tmp.emit(uid)  # create them ...
        # self.slot_ptr_moved_tmp(uid, self.__main_ptr_i)  # ... and __move

    def find_signal_worker(self, text: str) -> Optional[ABSignalSuit]:
        """Find signal by substring.

        :param text: Substring to search in signal names
        :return: SignalSuit found
        """
        for t in (self.analog_table, self.status_table):
            for bar in t.bars:
                if (not bar.hidden) and (ss := bar.find_signal(text)):
                    t.scrollTo(t.model().index(bar.row, 0))
                    return ss

    def __do_file_close(self):
        """Close this osc."""
        # self.close()  # close widget but not tab itself
        self.__father.slot_tab_close(self.parent().indexOf(self))  # QStackedWidget.ComtradeTabWidget

    def __do_file_info(self):
        """Show misc osc info."""

        def t_r(name: str, value: Any):
            """HTML <tr> constructor."""
            return f"<tr><th>{name}:</th><td>{value}</td></tr>"

        def __debug(i: int) -> str:
            sig = self.osc.y[i]
            a = sig.a_values(False)
            a_c = sig.a_values(True)
            return \
                f"Name: {sig.sid} (raw | centered)\n" \
                f"v_min=   {sig.v_min(False):8.3f} | {sig.v_min(True):8.3f}\n" \
                f"v_max=   {sig.v_max(False):8.3f} | {sig.v_max(True):8.3f}\n" \
                f"a_div=   {sig.a_div(False):8.3f} | {sig.a_div(True):8.3f}\n" \
                f"a_min=   {sig.a_min(False):8.3f} | {sig.a_min(True):8.3f}\n" \
                f"a_max=   {sig.a_max(False):8.3f} | {sig.a_max(True):8.3f}\n" \
                f"a_v_min= {sig.a_v_min(False):8.3f} | {sig.a_v_min(True):8.3f}\n" \
                f"a_v_max= {sig.a_v_max(False):8.3f} | {sig.a_v_max(True):8.3f}\n" \
                f"min_a=   {min(a):8.3f} | {min(a_c):8.3f}\n" \
                f"max_a=   {max(a):8.3f} | {max(a_c):8.3f}\n"

        # print(__debug(1))
        msg = QMessageBox(QMessageBox.Icon.Information, self.tr("Comtrade file info"), self.tr("Summary"))
        # plan A:
        # msg.setDetailedText(self.osc.cfg_summary())
        # plan B
        info = self.osc.info
        txt = "<html><body><table><tbody>"
        txt += t_r(self.tr("File"), self.osc.path)  # was self.osc.raw.cfg.filepath
        txt += t_r(self.tr("Station name"), info['station_name'])
        txt += t_r(self.tr("Station id"), info['rec_dev_id'])
        txt += t_r(self.tr("Comtrade ver."), info['rev_year'])
        txt += t_r(self.tr("File format"), self.osc.ft)
        txt += t_r(self.tr("Analog chs."), info['analog_count'])
        txt += t_r(self.tr("Status chs."), info['status_count'])
        txt += t_r(self.tr("Time"), f"{info['start_timestamp']}&hellip;{self.osc.trigger_timestamp}"
                                    f" with &times; {info['timemult']}")
        txt += t_r(self.tr("Time base"), info['time_base'])
        txt += t_r(self.tr("Line freq, Hz"), info['frequency'])
        txt += t_r(self.tr("Samples"), self.osc.total_samples)
        txt += t_r(self.tr("Sample rate"), f"{self.osc.rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()

    def __do_file_convert(self):
        """Convert the osc into opposite format (ASCII<>BINARY)."""
        fn = QFileDialog.getSaveFileName(
            self,
            self.tr("Save file as %s") % {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[self.osc.ft]
        )
        if fn[0]:
            try:
                convert(pathlib.Path(self.osc.filepath), pathlib.Path(fn[0]))
            except ConvertError as e:
                QMessageBox.critical(self, self.tr("Converting error"), str(e))

    def __do_file_csv(self):
        """Export the osc into CSV file."""
        fn = QFileDialog.getSaveFileName(
            self,
            self.tr("Export file as CSV"),
            str(pathlib.Path(self.osc.filepath).with_suffix('.csv')),
            self.tr("Comma separated values (*.csv)")
        )
        if fn[0]:
            export_to_csv(self.osc, self.show_sec, pathlib.Path(fn[0]))

    def __do_cfg_save(self):
        """Save osc settings."""
        fn = QFileDialog.getSaveFileName(
            self,
            self.tr("Save settings"),
            str(pathlib.Path(self.osc.filepath).with_suffix('.ofg')),
            self.tr("Oscillogramm configuration (*.ofg)")
        )
        if fn[0]:
            with open(fn[0], 'wt') as fp:  # FIXME: chk encoding
                json.dump(self.__ofg_store(), fp, indent=2)

    def __do_cfg_load(self):
        """[Re]load osc settings."""
        fn = QFileDialog.getOpenFileName(
            self,
            "Load settings",
            str(pathlib.Path(self.osc.filepath).parent),
            self.tr("Oscillogramm configuration (*.ofg)")
        )
        if fn[0]:
            with open(fn[0], 'rt') as fp:  # FIXME: encoding
                self.__ofg_restore(json.load(fp))

    def __do_signal_unhide(self):
        """Unhide all signals."""
        self.signal_unhide_all.emit()

    def __do_signal_find(self):
        """Open 'Find signal' dialog."""
        FindDialog(self).exec_()

    def __do_math_module(self):
        MathModuleDialog(self.ass_list).exec()

    def __do_resize_y_all_inc(self):
        self.analog_table.resize_y_all(True)
        self.status_table.resize_y_all(True)

    def __do_resize_y_all_dec(self):
        self.analog_table.resize_y_all(False)
        self.status_table.resize_y_all(False)

    def __do_xzoom_in(self):
        """X-zoom in action."""
        self.__update_xzoom(self.x_zoom - 1)

    def __do_xzoom_out(self):
        """X-zoom out action."""
        self.__update_xzoom(self.x_zoom + 1)

    def __do_centered(self, _: bool):
        self.osc.shifted = self.action_centered.isChecked()
        self.signal_chged_shift.emit()

    def __do_pors(self, _: QAction):
        self.show_sec = self.action_pors_sec.isChecked()
        self.signal_chged_pors.emit()

    def __do_viewas(self, a: QAction):
        self.viewas_toolbutton.setDefaultAction(a)
        self.viewas = a.data()
        self.signal_chged_func.emit()

    def __do_ptr_add_tmp(self):
        self.__ptr_add_tmp(max(self.__tmp_ptr_i.keys()) + 1 if self.__tmp_ptr_i.keys() else 1, self.__main_ptr_i)

    def __do_ptr_add_msr(self):
        if ss_selected := SelectSignalsDialog(self.ass_list).execute():
            for i in ss_selected:
                uid = max(self.msr_ptr_uids) + 1 if self.msr_ptr_uids else 1
                self.ass_list[i].add_ptr_msr(uid, self.main_ptr_i)

    def __do_ptr_add_lvl(self):
        if ss_selected := SelectSignalsDialog(self.ass_list).execute():
            for i in ss_selected:
                uid = max(self.lvl_ptr_uids) + 1 if self.lvl_ptr_uids else 1
                self.ass_list[i].add_ptr_lvl(uid)

    def __do_mainptr_l(self):
        if self.__main_ptr_i > 0:
            self.slot_ptr_moved_main(self.__main_ptr_i - 1)

    def __do_mainptr_r(self):
        if self.__main_ptr_i < (self.osc.total_samples - 1):
            self.slot_ptr_moved_main(self.__main_ptr_i + 1)

    def __do_vector_diagram(self):
        if not self.cvdwin:
            self.cvdwin = CVDWindow(self)
        self.action_vector_diagram.setEnabled(False)
        self.cvdwin.show()

    def __do_harmonic_diagram(self):
        if not self.hdwin:
            self.hdwin = HDWindow(self)
        self.action_harmonic_diagram.setEnabled(False)
        self.hdwin.show()

    def __do_value_table(self):
        VTWindow(self).exec_()

    def __do_omp_map(self):
        if not self.omp_ptr:
            return
        if not self.ompmapwin:
            self.ompmapwin = OMPMapWindow(self)
        self.ompmapwin.exec_()

    def __do_omp_save(self):
        if not self.omp_ptr:
            return
        if not self.ompmapwin:
            QMessageBox.critical(
                self,
                self.tr("OMP save error"),
                self.tr("OMP map was not call somewhen")
            )
            return
        if not self.ompmapwin.is_defined:
            QMessageBox.critical(
                self,
                self.tr("OMP save error"),
                self.tr("OMP map is not fully defined")
            )
            return
        fn = QFileDialog.getSaveFileName(
            self,
            self.tr("Save OMP values"),
            str(pathlib.Path(self.osc.filepath).with_suffix('.uim')),
            self.tr("U,I measurements (*.uim)")
        )
        if fn[0]:
            self.ompmapwin.data_save(pathlib.Path(fn[0]))

    def resize_col_ctrl(self, dx: int):
        """Resize left column in signal tables.

        Used by: ctrl.VLine
        """
        if self.col_ctrl_width + dx > iosc.const.COL0_WIDTH_MIN:
            self.col_ctrl_width += dx
            self.signal_resize_col_ctrl.emit(self.col_ctrl_width)

    def slot_ptr_moved_main(self, i: int):
        """Dispatch all main ptrs.

        :param i: New Main Ptr x-position
        :type i: ~~QCPItemPosition~~ int
        Emit slot_main_ptr_move(pos) for:
        - TimeAxisPlot (x)
        - SignalChartWidget (x) [=> SignalCtrlWidget(y)]
        - statusbar (x)
        """
        self.__main_ptr_i = i
        self.signal_ptr_moved_main.emit(i)

    def slot_ptr_moved_sc(self, i: int):
        """Dispatch all OMP SC ptrs.

        :param i: New SC Ptr index
        :type i: ~~QCPItemPosition~~ float
        Emit slot_sc_ptr_move(pos) for:
        - [TimeAxisPlot (x)]
        - SignalChartWidget
        """
        self.omp_ptr.i_sc = i
        self.signal_ptr_moved_sc.emit(i)
        self.signal_ptr_moved_pr.emit(self.omp_ptr.i_pr)

    def slot_ptr_moved_tmp(self, uid: int, i: int):
        """Move tmp pointer in child widgets.

        :param uid: TmpPtr uniq id
        :param i: Sample to move to
        Used by: ptr.TmpPtr
        """
        self.__tmp_ptr_i[uid] = i
        self.signal_ptr_moved_tmp.emit(uid, i)

    def slot_ptr_del_tmp(self, uid: int):
        """Del tmp pointer in all child widgets.

        :param uid: TmpPtr uniq id
        """
        del self.__tmp_ptr_i[uid]
        self.signal_ptr_del_tmp.emit(uid)

    def slot_ptr_edit_tmp(self, uid: int):
        """Edit tmp pointer.

        :param uid: TmpPtr uniq id
        """
        v = self.i2x(self.__tmp_ptr_i[uid])
        name = self.timeaxis_bar.plot.get_tmp_ptr_name(uid)
        form = TmpPtrDialog((v, self.osc.x_min, self.osc.x_max, 1000 / self.osc.rate, name))
        if form.exec_():
            self.timeaxis_bar.plot.set_tmp_ptr_name(uid, form.f_name.text())
            self.signal_ptr_moved_tmp.emit(uid, self.x2i(form.f_val.value()))

    def hideEvent(self, event: QHideEvent):
        """Hide child windows on osc switch out."""
        super().hideEvent(event)
        if self.cvdwin and self.cvdwin.isVisible():
            self.cvdwin.hide()
        if self.hdwin and self.hdwin.isVisible():
            self.hdwin.hide()

    def showEvent(self, event: QShowEvent):
        """Show child windows on osc switch in."""
        super().showEvent(event)
        if not self.action_vector_diagram.isEnabled():  # == CVD opened
            self.cvdwin.show()
        if not self.action_harmonic_diagram.isEnabled():  # == HD opened
            self.hdwin.show()

    def closeEvent(self, event: QCloseEvent):
        """Close child windows."""
        if self.cvdwin:
            self.cvdwin.deleteLater()
        if self.hdwin:
            self.hdwin.deleteLater()
        super().closeEvent(event)

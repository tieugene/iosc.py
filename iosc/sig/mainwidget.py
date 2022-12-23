"""Signal tab widget
RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import json
import pathlib
from typing import Any, Dict, Optional, List
# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QCloseEvent, QHideEvent, QShowEvent, QColor, QRgba64
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMenuBar, QToolBar, QAction, QMessageBox, QFileDialog,\
    QHBoxLayout, QActionGroup, QToolButton, QMenu
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.core.tocsv import export_to_csv
from iosc.icon import svg_icon, ESvgSrc
from iosc.core.convtrade import convert, ConvertError
from iosc.sig.pdfout.dialog import PDFOutPreviewDialog
from iosc.sig.pdfout.pdfprinter import PdfPrinter
from iosc.sig.tools.cvdwindow import CVDWindow
from iosc.sig.tools.hdwindow import HDWindow
from iosc.sig.tools.ompmap import OMPMapWindow
from iosc.sig.tools.vtwindow import VTWindow
from iosc.sig.widget.section import TimeAxisBar, SignalBarTable, TimeStampsBar, XScroller
from iosc.sig.widget.common import AnalogSignalSuit, StatusSignalSuit
from iosc.sig.widget.dialog import TmpPtrDialog, SelectSignalsDialog


class ComtradeWidget(QWidget):
    """Main osc window."""
    # inner vars
    osc: mycomtrade.MyComtrade
    col_ctrl_width: int
    # inner vars
    __main_ptr_i: int  # current Main Ptr index in source arrays
    __sc_ptr_i: Optional[int]  # current OMP SC Ptr index in source arrays
    __tmp_ptr_i: dict[int, int]  # current Tmp Ptr indexes in source arrays: ptr_uid => x_idx
    msr_ptr_uids: set[int]  # MsrPtr uids
    lvl_ptr_uids: set[int]  # LvlPtr uids
    __omp_width: Optional[int]  # distance from OMP PR and SC pointers, periods
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
    action_shift: QActionGroup
    action_shift_not: QAction
    action_shift_yes: QAction
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
    action_vector_diagram: QAction
    action_harmonic_diagram: QAction
    action_value_table: QAction
    action_omp_map: QAction
    action_omp_save: QAction
    action_signal_find: QAction
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
    signal_ptr_add_tmp = pyqtSignal(int)  # add new TmpPtr in each SignalChartWidget
    signal_ptr_del_tmp = pyqtSignal(int)  # rm TmpPtr from each SignalChartWidget
    signal_ptr_moved_tmp = pyqtSignal(int, int)  # refresh SignalChartWidget on Tmp Ptr moved

    def __init__(self, osc: mycomtrade.MyComtrade, parent: 'ComtradeTabWidget'):
        super().__init__(parent)
        self.osc = osc
        self.col_ctrl_width = iosc.const.COL0_WIDTH_INIT
        self.__main_ptr_i = self.x2i(0.0)  # default: Z (Osc1: 600)
        if osc.chk_gap_l() or osc.chk_gap_r():
            self.__sc_ptr_i = self.__omp_width = None
        else:
            self.__sc_ptr_i = self.__main_ptr_i + 2 * self.osc.spp
            self.__omp_width = 3
        self.__tmp_ptr_i = dict()
        self.msr_ptr_uids = set()
        self.lvl_ptr_uids = set()
        self.__shifted = False
        self.x_zoom = len(iosc.const.X_PX_WIDTH_uS) - 1  # initial: max
        self.show_sec = True
        self.viewas = 0
        self.ass_list = list()
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_toolbar()
        self.__set_data()
        self.__update_xzoom_actions()
        self.__mk_connections()

    def x_px_width_us(self) -> int:
        """Current px width, μs"""
        return iosc.const.X_PX_WIDTH_uS[self.x_zoom]

    # property
    def x_width_px(self) -> int:
        """Current graph width, px (?)"""
        return round(self.osc.x_size * 1000 / self.x_px_width_us())

    # property
    def x_sample_width_px(self) -> int:
        """Current width of samples interval, px"""
        return round(self.x_width_px() / self.osc.raw.total_samples)

    @property
    def main_ptr_i(self) -> int:
        return self.__main_ptr_i

    @property
    def main_ptr_x(self) -> float:
        return self.i2x(self.__main_ptr_i)

    @property
    def tmp_ptr_i(self) -> Dict[int, int]:
        return self.__tmp_ptr_i

    @property
    def sc_ptr_i(self) -> Optional[int]:
        """Position index of master (SC, right) OMP pointer"""
        return self.__sc_ptr_i

    @property
    def sc_ptr_x(self) -> Optional[float]:
        """Time of master (right) OMP pointer"""
        if self.__sc_ptr_i:
            return self.i2x(self.__sc_ptr_i)

    @property
    def omp_width(self) -> Optional[int]:
        """Distance between SC pointers, periods"""
        return self.__omp_width

    @omp_width.setter
    def omp_width(self, i):
        # self.__omp_width = i
        # self.signal_omp_width_changed.emit()
        print(i)  # TODO: UB

    @property
    def pr_ptr_i(self) -> Optional[int]:
        """Position index of slave (left) OMP pointer"""
        if self.__sc_ptr_i is not None:
            return self.__sc_ptr_i + self.osc.spp * self.__omp_width

    @property
    def shifted(self):
        return self.osc.shifted

    def x2i(self, x: float) -> int:
        """Recalc graph x-position (ms) into index in signal array"""
        return int(round((x - self.osc.x_min) / 1000 * self.osc.rate))

    def i2x(self, i: int) -> float:
        """Recalc index in signal array int graph x-position (ms)"""
        return self.osc.x[i]

    def __mk_widgets(self):
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
        self.action_close = QAction(QIcon.fromTheme("window-close"),
                                    "&Close",
                                    self,
                                    shortcut="Ctrl+W",
                                    triggered=self.__do_file_close)
        self.action_info = QAction(QIcon.fromTheme("dialog-information"),
                                   "&Info",
                                   self,
                                   shortcut="Ctrl+I",
                                   triggered=self.__do_file_info)
        self.action_convert = QAction(QIcon.fromTheme("document-save-as"),
                                      "&Save as...",
                                      self,
                                      triggered=self.__do_file_convert)
        self.action_csv = QAction("&Export to CSV",
                                  self,
                                  triggered=self.__do_file_csv)
        self.action_cfg_save = QAction(QIcon.fromTheme("document-save"),
                                       "&Save settings",
                                       self,
                                       shortcut="Ctrl+S",
                                       triggered=self.__do_cfg_save)
        self.action_cfg_load = QAction(QIcon.fromTheme("document-open"),
                                       "&Load settings",
                                       self,
                                       shortcut="Ctrl+L",
                                       triggered=self.__do_cfg_load)
        self.action_pdfout = QAction(svg_icon(ESvgSrc.PDF),
                                     "&Print...",
                                     self,
                                     shortcut="Ctrl+P",
                                     triggered=self.__print_preview.open)
        self.action_resize_y_in = QAction(svg_icon(ESvgSrc.VZoomIn),
                                          "Y-Resize +",
                                          self,
                                          triggered=self.__do_resize_y_all_inc)
        self.action_resize_y_out = QAction(svg_icon(ESvgSrc.VZoomOut),
                                           "Y-Resize -",
                                           self,
                                           triggered=self.__do_resize_y_all_dec)
        self.action_zoom_x_in = QAction(svg_icon(ESvgSrc.HZoomIn),
                                        "X-Zoom in",
                                        self,
                                        triggered=self.__do_xzoom_in)
        self.action_zoom_x_out = QAction(svg_icon(ESvgSrc.HZoomOut),
                                         "X-Zoom out",
                                         self,
                                         triggered=self.__do_xzoom_out)
        self.action_unhide = QAction(QIcon.fromTheme("edit-undo"),
                                     "&Unhide all",
                                     self,
                                     triggered=self.__do_unhide)
        self.action_shift_not = QAction(svg_icon(ESvgSrc.ShiftOrig),
                                        "&Original",
                                        self,
                                        checkable=True)
        self.action_shift_yes = QAction(svg_icon(ESvgSrc.ShiftCentered),
                                        "&Centered",
                                        self,
                                        checkable=True)
        self.action_pors_pri = QAction(svg_icon(ESvgSrc.PorsP),
                                       "&Pri",
                                       self,
                                       checkable=True)
        self.action_pors_sec = QAction(svg_icon(ESvgSrc.PorsS),
                                       "&Sec",
                                       self,
                                       checkable=True)
        self.action_viewas_is = QAction("As &is",
                                        self,
                                        checkable=True)
        self.action_viewas_mid = QAction("&Mid",
                                         self,
                                         checkable=True)
        self.action_viewas_eff = QAction("&Eff",
                                         self,
                                         checkable=True)
        self.action_viewas_hrm1 = QAction("Hrm &1",
                                          self,
                                          checkable=True)
        self.action_viewas_hrm2 = QAction("Hrm &2",
                                          self,
                                          checkable=True)
        self.action_viewas_hrm3 = QAction("Hrm &3",
                                          self,
                                          checkable=True)
        self.action_viewas_hrm5 = QAction("Hrm &5",
                                          self,
                                          checkable=True)
        self.action_ptr_add_tmp = QAction("Add temporary pointer",
                                          self,
                                          triggered=self.__do_ptr_add_tmp)
        self.action_ptr_add_msr = QAction("Add measure pointers",
                                          self,
                                          triggered=self.__do_ptr_add_msr)
        self.action_ptr_add_lvl = QAction("Add level pointers",
                                          self,
                                          triggered=self.__do_ptr_add_lvl)
        self.action_vector_diagram = QAction("Vector chart",
                                             self,
                                             shortcut="Ctrl+V",
                                             triggered=self.__do_vector_diagram)
        self.action_harmonic_diagram = QAction("Harmonic chart",
                                               self,
                                               shortcut="Ctrl+H",
                                               triggered=self.__do_harmonic_diagram)
        self.action_value_table = QAction(QIcon.fromTheme("x-office-spreadsheet"),
                                          "Value table",
                                          self,
                                          shortcut="Ctrl+T",
                                          triggered=self.__do_value_table)
        self.action_omp_map = QAction("OMP map",
                                      self,
                                      shortcut="Ctrl+M",
                                      triggered=self.__do_omp_map)
        self.action_omp_save = QAction("OMP save",
                                       self,
                                       triggered=self.__do_omp_save)
        self.action_signal_find = QAction("Find...",
                                          self,
                                          shortcut="Ctrl+F",
                                          triggered=self.__do_signal_find)
        self.action_shift = QActionGroup(self)
        self.action_shift.addAction(self.action_shift_not).setChecked(True)
        self.action_shift.addAction(self.action_shift_yes)
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
        self.action_omp_map.setEnabled(self.__sc_ptr_i is not None)
        self.action_omp_save.setEnabled(self.__sc_ptr_i is not None)

    def __mk_menu(self):
        menu_file = self.menubar.addMenu("&File")
        menu_file.addAction(self.action_info)
        menu_file.addAction(self.action_convert)
        menu_file.addAction(self.action_csv)
        menu_file.addAction(self.action_cfg_save)
        menu_file.addAction(self.action_cfg_load)
        menu_file.addAction(self.action_pdfout)
        menu_file.addAction(self.action_close)
        menu_view = self.menubar.addMenu("&View")
        menu_view.addAction(self.action_resize_y_in)
        menu_view.addAction(self.action_resize_y_out)
        menu_view.addAction(self.action_zoom_x_in)
        menu_view.addAction(self.action_zoom_x_out)
        menu_view_shift = menu_view.addMenu("Original/Shifted")
        menu_view_shift.addAction(self.action_shift_not)
        menu_view_shift.addAction(self.action_shift_yes)
        menu_view_pors = menu_view.addMenu("Pri/Sec")
        menu_view_pors.addAction(self.action_pors_pri)
        menu_view_pors.addAction(self.action_pors_sec)
        menu_view_viewas = menu_view.addMenu("View as...")
        menu_view_viewas.addAction(self.action_viewas_is)
        menu_view_viewas.addAction(self.action_viewas_mid)
        menu_view_viewas.addAction(self.action_viewas_eff)
        menu_view_viewas.addAction(self.action_viewas_hrm1)
        menu_view_viewas.addAction(self.action_viewas_hrm2)
        menu_view_viewas.addAction(self.action_viewas_hrm3)
        menu_view_viewas.addAction(self.action_viewas_hrm5)
        menu_signal = self.menubar.addMenu("&Signal")
        menu_signal.addAction(self.action_unhide)
        menu_signal.addAction(self.action_signal_find)
        menu_ptr = self.menubar.addMenu("&Pointers")
        menu_ptr.addAction(self.action_ptr_add_tmp)
        menu_ptr.addAction(self.action_ptr_add_msr)
        menu_ptr.addAction(self.action_ptr_add_lvl)
        menu_tools = self.menubar.addMenu("&Tools")
        menu_tools.addAction(self.action_vector_diagram)
        menu_tools.addAction(self.action_harmonic_diagram)
        menu_tools.addAction(self.action_value_table)
        menu_tools.addAction(self.action_omp_map)
        menu_tools.addAction(self.action_omp_save)

    def __mk_toolbar(self):
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
        self.toolbar.addAction(self.action_shift_not)
        self.toolbar.addAction(self.action_shift_yes)
        self.toolbar.addAction(self.action_pors_pri)
        self.toolbar.addAction(self.action_pors_sec)
        self.toolbar.addWidget(self.viewas_toolbutton)
        self.toolbar.addAction(self.action_info)

    def __mk_connections(self):
        self.action_shift.triggered.connect(self.__do_shift)
        self.action_pors.triggered.connect(self.__do_pors)
        self.action_viewas.triggered.connect(self.__do_viewas)
        self.xscroll_bar.valueChanged.connect(self.timeaxis_bar.plot.slot_rerange_force)
        self.xscroll_bar.valueChanged.connect(self.timestamps_bar.plot.slot_rerange_force)
        self.xscroll_bar.signal_update_plots.connect(self.timeaxis_bar.plot.slot_rerange)
        self.xscroll_bar.signal_update_plots.connect(self.timestamps_bar.plot.slot_rerange)

    def __set_data(self):
        for sig in self.osc.y:
            if not sig.is_bool:
                self.analog_table.bar_insert().sig_add(ass := AnalogSignalSuit(sig, self))  # FIXME: default height
                self.ass_list.append(ass)
            else:
                self.status_table.bar_insert().sig_add(StatusSignalSuit(sig, self))  # FIXME: default height

    def __ofg_store(self) -> dict:
        """:todo: capsulate"""
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
            'table': list()
        }
        if self.__sc_ptr_i is not None:
            data['ptr']['omp'] = {'i': self.__sc_ptr_i, 'w': self.__omp_width}
        if self.__tmp_ptr_i:
            tmp = {}
            for uid, i in self.__tmp_ptr_i.items():
                tmp[uid] = i  # FIXME: {'uid': ..., 'xi': ...}
            data['ptr']['tmp'] = tmp
        # bars
        for table in (self.analog_table, self.status_table):
            t_data = list()
            for bar in table.bars:
                b_data = {'s': list()}
                if not bar.is_bool():
                    b_data['h'] = bar.height
                    b_data['yzoom'] = bar.zoom_y
                for ss in bar.signals:
                    s_data = {
                        'i': ss.signal.i,
                        'num': ss.num,  # FIXME: ×?
                        'show': not ss.hidden,
                        'color': int(ss.color.rgba64()),
                    }
                    if not ss.signal.is_bool:
                        s_data['style'] = ss.line_style
                        if ss.msr_ptr:
                            ptrs = dict()
                            for uid, v in ss.msr_ptr.items():
                                ptrs[uid] = {'i': v[1], 'f': v[2]}  # FIXME: {'uid': ...}
                            s_data['ptr_msr'] = ptrs
                        if ss.lvl_ptr:
                            ptrs = dict()
                            for uid, v in ss.lvl_ptr.items():
                                ptrs[uid] = v[1]  # FIXME: {'uid': ...}
                            s_data['ptr_lvl'] = ptrs
                    b_data['s'].append(s_data)
                t_data.append(b_data)
            data['table'].append(t_data)
        # tools
        tool = dict()
        # - CDV
        if self.cvdwin:
            tool['cvd'] = {
                'show': self.cvdwin.isVisible(),
                'base': self.cvdwin.ss_base.signal.i,
                'used': [ss.signal.i for ss in self.cvdwin.ss_used]
            }
        # - HD
        if self.hdwin:
            tool['hd'] = {
                'show': self.hdwin.isVisible(),
                'used': [ss.signal.i for ss in self.hdwin.ss_used]
            }
        # - OMP
        if self.ompmapwin:
            tool['omp'] = {
                'show': self.ompmapwin.isVisible(),
                'used': self.ompmapwin.map
            }
        if tool:
            data['tool'] = tool
        return data

    def __cfg_restore(self, data: dict):
        """Restore osc from (.ofg.
        :todo: capsulate"""
        if data['ver'] != iosc.const.OFG_VER:
            QMessageBox.critical(self, "OFG loading error", f"Incompatible version: {data['ver']}")
        # 1. clean
        # 1.1. Tmp ptrs
        for uid in self.__tmp_ptr_i.keys():
            self.slot_ptr_del_tmp(uid)
        # 1.2. store SS' | detch them | drop bars
        sss = [None] * len(self.osc.y)
        for table in (self.analog_table, self.status_table):
            for bar in table.bars[::-1]:  # reverse order
                for ss in bar.signals:
                    sss[ss.signal.i] = ss
                    if not ss.signal.is_bool:
                        for uid in ss.msr_ptr.keys():  # TODO: check 'n/a'
                            ss.del_ptr_msr(uid)
                        for uid in ss.lvl_ptr.keys():  # TODO: check 'n/a'
                            ss.del_ptr_lvl(uid)
                    ss.detach()
                bar.suicide()
        # 1.3. Tools
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
                    if not ss.signal.is_bool:
                        ss.line_style = src_ss['style']  # style
                        for uid, v in src_ss.get('ptr_msr', {}).items():
                            ss.add_ptr_msr(int(uid), v['i'], v['f'])
                        for uid, v in src_ss.get('ptr_lvl', {}).items():
                            ss.add_ptr_lvl(int(uid), v)
                if not dst_bar.is_bool():
                    dst_bar.height = src_bar['h']  # height
                    dst_bar.zoom_y = src_bar['yzoom']  # yzoom
        # 2.1. Window
        self.__update_xzoom(data['xzoom'])  # - x-zoom
        # - modes
        # -- shift
        if data['mode']['shift']:
            self.action_shift_yes.setChecked(True)
        else:
            self.action_shift_not.setChecked(True)
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
        if self.__sc_ptr_i is not None:
            self.slot_ptr_moved_sc(data['ptr']['omp']['i'])
            # TODO: width
        # - Tmp ptrs
        for uid, i in data['ptr'].get('tmp', {}).items():
            self.__ptr_add_tmp(int(uid), i)
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

    def __update_xzoom_actions(self):
        """Set X-zoom actions availability"""
        self.action_zoom_x_in.setEnabled(self.x_zoom > 0)
        self.action_zoom_x_out.setEnabled(self.x_zoom < (len(iosc.const.X_PX_WIDTH_uS) - 1))

    def __update_xzoom(self, xz):
        """Change X-zoom.
        :param xz: New X-zoom value
        :todo: add force:bool=False
        """
        if (xz != self.x_zoom) and (0 <= xz < len(iosc.const.X_PX_WIDTH_uS)):
            self.x_zoom = xz
            self.__update_xzoom_actions()
            self.signal_x_zoom.emit()

    def __ptr_add_tmp(self, uid: int, i: int):
        """:todo: optional name:str"""
        self.__tmp_ptr_i[uid] = i
        self.signal_ptr_add_tmp.emit(uid)  # create them ...
        # self.slot_ptr_moved_tmp(uid, self.__main_ptr_i)  # ... and __move

    def __do_file_close(self):
        # self.close()  # close widget but not tab itself
        self.parent().parent().slot_tab_close(self.parent().indexOf(self))  # QStackedWidget.ComtradeTabWidget

    def __do_file_info(self):
        def tr(name: str, value: Any):
            return f"<tr><th>{name}:</th><td>{value}</td></tr>"

        msg = QMessageBox(QMessageBox.Icon.Information, "Comtrade file info", "Summary")
        # plan A:
        # msg.setDetailedText(self.osc.cfg_summary())
        # plan B
        txt = "<html><body><table><tbody>"
        txt += tr("File", self.osc.path)  # was self.osc.raw.cfg.filepath
        txt += tr("Station name", self.osc.raw.station_name)
        txt += tr("Station id", self.osc.raw.rec_dev_id)
        txt += tr("Comtrade ver.", self.osc.raw.rev_year)
        txt += tr("File format", self.osc.raw.ft)
        txt += tr("Analog chs.", self.osc.raw.analog_count)
        txt += tr("Status chs.", self.osc.raw.status_count)
        txt += tr("Time", f"{self.osc.raw.start_timestamp}&hellip;{self.osc.raw.trigger_timestamp}"
                          f" with &times; {self.osc.raw.cfg.timemult}")
        txt += tr("Time base", self.osc.raw.time_base)
        txt += tr("Line freq, Hz", self.osc.raw.frequency)
        txt += tr("Samples", self.osc.raw.total_samples)
        txt += tr(f"Sample rate:", f"{self.osc.rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()

    def __do_file_convert(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Save file as %s" % {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[self.osc.raw.ft]
        )
        if fn[0]:
            try:
                convert(pathlib.Path(self.osc.raw.cfg.filepath), pathlib.Path(fn[0]))
            except ConvertError as e:
                QMessageBox.critical(self, "Converting error", str(e))

    def __do_file_csv(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export file as CSV",
            str(pathlib.Path(self.osc.raw.cfg.filepath).with_suffix('.csv')),
            "Comma separated values (*.csv)"
        )
        if fn[0]:
            export_to_csv(self.osc, self.show_sec, pathlib.Path(fn[0]))

    def __do_cfg_save(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Save settings",
            str(pathlib.Path(self.osc.raw.cfg.filepath).with_suffix('.ofg')),
            "Oscillogramm configuration (*.ofg)"
        )
        if fn[0]:
            with open(fn[0], 'wt') as fp:
                json.dump(self.__ofg_store(), fp, indent=2)

    def __do_cfg_load(self):
        fn = QFileDialog.getOpenFileName(
            self,
            "Load settings",
            str(pathlib.Path(self.osc.raw.cfg.filepath).parent),
            "Oscillogramm configuration (*.ofg)"
        )
        if fn[0]:
            with open(fn[0], 'rt') as fp:
                self.__cfg_restore(json.load(fp))

    def __do_unhide(self):
        self.signal_unhide_all.emit()

    def __do_signal_find(self):
        """
        SignalBarTable:
        - frameShape() == 6 (StyledPanel)
        - frameWidth() == 2
        - midLineWidth() == 0
        :return:
        """
        for t in (self.analog_table, self.status_table):
            if t.hasFocus():
                t.do_find_signal()
                break

    def __do_resize_y_all_inc(self):
        self.analog_table.resize_y_all(True)
        self.status_table.resize_y_all(True)

    def __do_resize_y_all_dec(self):
        self.analog_table.resize_y_all(False)
        self.status_table.resize_y_all(False)

    def __do_xzoom_in(self):
        """X-zoom in action"""
        self.__update_xzoom(self.x_zoom-1)

    def __do_xzoom_out(self):
        """X-zoom out action"""
        self.__update_xzoom(self.x_zoom+1)

    def __do_shift(self, _: QAction):
        self.osc.shifted = self.action_shift_yes.isChecked()
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
        if self.__sc_ptr_i is None:
            return
        if not self.ompmapwin:
            self.ompmapwin = OMPMapWindow(self)
        self.ompmapwin.exec_()

    def __do_omp_save(self):
        if self.__sc_ptr_i is None:
            return
        if not self.ompmapwin:
            QMessageBox.critical(self, "OMP save error", "OMP map was not call somewhen")
            return
        if -1 in self.ompmapwin.map:
            QMessageBox.critical(self, "OMP save error", "OMP map is not fully defined")
            return
        fn = QFileDialog.getSaveFileName(
            self,
            "Save OMP values",
            str(pathlib.Path(self.osc.raw.cfg.filepath).with_suffix('.uim')),
            "U,I mesurements (*.uim)"
        )
        if fn[0]:
            self.ompmapwin.data_save(pathlib.Path(fn[0]))

    def resize_col_ctrl(self, dx: int):
        if self.col_ctrl_width + dx > iosc.const.COL0_WIDTH_MIN:
            self.col_ctrl_width += dx
            self.signal_resize_col_ctrl.emit(self.col_ctrl_width)

    def slot_ptr_moved_main(self, i: int):
        """
        Dispatch all main ptrs
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
        """
        Dispatch all OMP SC ptrs
        :param i: New SC Ptr index
        :type i: ~~QCPItemPosition~~ float
        Emit slot_sc_ptr_move(pos) for:
        - [TimeAxisPlot (x)]
        - SignalChartWidget
        """
        self.__sc_ptr_i = i
        self.signal_ptr_moved_sc.emit(i)

    def slot_ptr_moved_tmp(self, uid: int, i: int):
        self.__tmp_ptr_i[uid] = i
        self.signal_ptr_moved_tmp.emit(uid, i)

    def slot_ptr_del_tmp(self, uid: int):
        del self.__tmp_ptr_i[uid]
        self.signal_ptr_del_tmp.emit(uid)

    def slot_ptr_edit_tmp(self, uid: int):
        v = self.i2x(self.__tmp_ptr_i[uid])
        name = self.timeaxis_bar.plot.get_tmp_ptr_name(uid)
        form = TmpPtrDialog((v, self.osc.x_min, self.osc.x_max, 1000 / self.osc.rate, name))
        if form.exec_():
            self.timeaxis_bar.plot.set_tmp_ptr_name(uid, form.f_name.text())
            self.signal_ptr_moved_tmp.emit(uid, self.x2i(form.f_val.value()))

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        if self.cvdwin and self.cvdwin.isVisible():
            self.cvdwin.hide()
        if self.hdwin and self.hdwin.isVisible():
            self.hdwin.hide()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if not self.action_vector_diagram.isEnabled():  # == CVD opened
            self.cvdwin.show()
        if not self.action_harmonic_diagram.isEnabled():  # == HD opened
            self.hdwin.show()

    def closeEvent(self, event: QCloseEvent):
        if self.cvdwin:
            self.cvdwin.deleteLater()
        if self.hdwin:
            self.hdwin.deleteLater()
        super().closeEvent(event)

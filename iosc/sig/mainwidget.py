"""Signal tab widget
RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import cmath
import math
import pathlib
from typing import Any, Optional, Dict
# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMenuBar, QToolBar, QAction, QMessageBox, \
    QFileDialog, QHBoxLayout, QActionGroup, QToolButton, QMenu
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.core.sigfunc import func_list
from iosc.icon import svg_icon, ESvgSrc
from iosc.core.convtrade import convert, ConvertError
from iosc.sig.section import TimeAxisBar, SignalBarTable, TimeStampsBar, XScroller
from iosc.sig.widget.common import SignalSuit
from iosc.sig.widget.dialog import TmpPtrDialog, SelectSignalsDialog


class ComtradeWidget(QWidget):
    """Main osc window."""
    # inner cons
    osc: mycomtrade.MyComtrade
    col_ctrl_width: int
    __path: pathlib.Path
    __tpp: int  # tics (samples) per signal period
    # inner vars
    __main_ptr_i: int  # current Main Ptr index in source arrays
    __sc_ptr_i: int  # current OMP SC Ptr index in source arrays
    __tmp_ptr_i: dict[int, int]  # current Tmp Ptr indexes in source arrays: ptr_uid => x_idx
    msr_ptr_uids: set[int]  # MsrPtr uids
    lvl_ptr_uids: set[int]  # LvlPtr uids
    __omp_width: int  # distance from OMP PR and SC pointers, periods
    __shifted: bool  # original/shifted selector
    __chart_width: Optional[int]  # width (px) of nested QCP charts
    x_zoom: int
    sig_no2widget: tuple[list, list]  # Translate signal no to chart widget
    show_sec: bool  # pri/sec selector
    viewas: int  # TODO: enum
    # actions
    action_close: QAction
    action_info: QAction
    action_convert: QAction
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
    # widgets
    menubar: QMenuBar
    toolbar: QToolBar
    viewas_toolbutton: QToolButton
    timeaxis_bar: TimeAxisBar
    analog_table: SignalBarTable
    status_table: SignalBarTable
    timestamps_bar: TimeStampsBar
    xscroll_bar: XScroller
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
    signal_xscale = pyqtSignal(int, int)  # set signal chart widths

    def __init__(self, osc: mycomtrade.MyComtrade, path: pathlib.Path, parent: 'ComtradeTabWidget'):
        super().__init__(parent)
        self.osc = osc
        self.col_ctrl_width = iosc.const.COL0_WIDTH_INIT
        self.__path = path
        self.__tpp = int(round(self.osc.raw.cfg.sample_rates[0][0] / self.osc.raw.cfg.frequency))
        self.__main_ptr_i = self.x2i(0.0)  # default: Z
        self.__sc_ptr_i = self.__main_ptr_i + 2 * self.__tpp
        self.__tmp_ptr_i = dict()
        self.msr_ptr_uids = set()
        self.lvl_ptr_uids = set()
        self.__omp_width = 3
        # ?self.__chart_width = None  # wait for line_up
        self.x_zoom = len(iosc.const.X_PX_WIDTH_uS) - 1  # initial: max
        self.__shifted = False
        self.show_sec = True
        self.viewas = 0
        self.__mk_widgets()
        self.__mk_layout()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_toolbar()
        self.__set_data()
        self.__update_xzoom_actions()
        self.__mk_connections()

    @property
    def i_max(self) -> int:
        return len(self.osc.x) - 1

    # property
    def x_min(self) -> float:
        return self.osc.x[0]

    # property
    def x_max(self) -> float:
        return self.osc.x[-1]

    # property
    def x_step(self) -> float:
        return 1000 / self.osc.raw.cfg.sample_rates[0][0]

    # property
    def x_width_ms(self) -> float:
        return self.x_max() - self.x_min()

    # property
    def x_width_px(self) -> int:
        return round(self.x_width_ms() * 1000 / iosc.const.X_PX_WIDTH_uS[self.x_zoom])

    # property
    def x_sample_width_px(self) -> int:
        """Current width of samples interval in px"""
        return round(self.x_width_px() / self.osc.raw.cfg.sample_rates[0][0])

    @property
    def tpp(self) -> int:
        return self.__tpp

    @property
    def main_ptr_i(self) -> int:
        return self.__main_ptr_i

    @property
    def main_ptr_x(self) -> float:
        return self.i2x(self.__main_ptr_i)

    @property
    def sc_ptr_i(self) -> int:
        return self.__sc_ptr_i

    @property
    def sc_ptr_x(self) -> float:
        return self.i2x(self.__sc_ptr_i)

    @property
    def tmp_ptr_i(self) -> Dict[int, int]:
        return self.__tmp_ptr_i

    @property
    def omp_width(self) -> int:
        return self.__omp_width

    @omp_width.setter
    def omp_width(self, i):
        # self.__omp_width = i
        # self.signal_omp_width_changed.emit()
        print(i)

    @property
    def shifted(self):
        return self.osc.shifted

    @property
    def chart_width(self):
        return self.__chart_width * self.x_zoom if self.__chart_width is not None else None

    def x2i(self, x: float) -> int:
        """Recalc graph x-position (ms) into index in signal array"""
        return int(round((self.osc.raw.trigger_time + x / 1000) * self.osc.rate[0][0]))

    def i2x(self, i: int) -> float:
        """Recalc index in signal array int graph x-position (ms)"""
        return 1000 * (self.osc.raw.time[i] - self.osc.raw.trigger_time)

    def sig2str(self, sig: mycomtrade.AnalogSignal, y: float) -> str:
        """Return string repr of signal dependong on:
         - signal value
         - pors (global)
         - orig/shifted (global, indirect)"""
        pors_y = y * sig.get_mult(self.show_sec)
        uu = sig.uu_orig
        if abs(pors_y) < 1:
            pors_y *= 1000
            uu = 'm' + uu
        elif abs(pors_y) > 1000:
            pors_y /= 1000
            uu = 'k' + uu
        return "%.3f %s" % (pors_y, uu)

    def sig2str_i(self, sig: mycomtrade.AnalogSignal, i: int, func_i: int) -> str:
        """Return string repr of signal dependong on:
         - signal value
         - in index i
         - selected function[func_i]
         - pors (global)
         - orig/shifted (global, indirect)"""
        func = func_list[func_i]
        v = func(sig.value, i, self.tpp)
        if isinstance(v, complex):  # hrm1
            y = abs(v)
        else:
            y = v
        y_str = self.sig2str(sig, y)
        if isinstance(v, complex):  # hrm1
            return "%s / %.3f°" % (y_str, math.degrees(cmath.phase(v)))
        else:
            return y_str

    def __mk_widgets(self):
        self.menubar = QMenuBar()
        self.toolbar = QToolBar(self)
        self.viewas_toolbutton = QToolButton(self)
        self.timeaxis_bar = TimeAxisBar(self)
        self.analog_table = SignalBarTable(self)
        self.status_table = SignalBarTable(self)
        self.timestamps_bar = TimeStampsBar(self)
        self.xscroll_bar = XScroller(self)

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
                                      shortcut="Ctrl+S",
                                      triggered=self.__do_file_convert)
        self.action_resize_y_in = QAction(svg_icon(ESvgSrc.VZoomIn),
                                       "Y-Zoom &in",
                                          self,
                                          statusTip="Vertical zoom in all",
                                          triggered=self.__do_ysize_all_in)
        self.action_resize_y_out = QAction(svg_icon(ESvgSrc.VZoomOut),
                                        "Y-Zoom &out",
                                           self,
                                           statusTip="Vertical zoom out all",
                                           triggered=self.__do_ysize_all_out)
        self.action_zoom_x_in = QAction(svg_icon(ESvgSrc.HZoomIn),
                                       "X-Zoom in",
                                        self,
                                        statusTip="Horizontal zoom in all",
                                        triggered=self.__do_xzoom_in)
        self.action_zoom_x_out = QAction(svg_icon(ESvgSrc.HZoomOut),
                                        "X-Zoom out",
                                         self,
                                         statusTip="Horizontal zoom out all",
                                         triggered=self.__do_xzoom_out)
        self.action_unhide = QAction(QIcon.fromTheme("edit-undo"),
                                     "&Unhide all",
                                     self,
                                     statusTip="Show hidden channels",
                                     triggered=self.__do_unhide)
        self.action_shift_not = QAction(svg_icon(ESvgSrc.ShiftOrig),
                                        "&Original",
                                        self,
                                        checkable=True,
                                        statusTip="Use original signal")
        self.action_shift_yes = QAction(svg_icon(ESvgSrc.ShiftCentered),
                                        "&Centered",
                                        self,
                                        checkable=True,
                                        statusTip="Use shifted signal")
        self.action_pors_pri = QAction(svg_icon(ESvgSrc.PorsP),
                                       "&Pri",
                                       self,
                                       checkable=True,
                                       statusTip="Show primary signal value")
        self.action_pors_sec = QAction(svg_icon(ESvgSrc.PorsS),
                                       "&Sec",
                                       self,
                                       checkable=True,
                                       statusTip="Show secondary signal values")
        self.action_viewas_is = QAction(QIcon(),
                                        "As &is",
                                        self,
                                        checkable=True,
                                        statusTip="Show current signal value")
        self.action_viewas_mid = QAction(QIcon(),
                                         "&Mid",
                                         self,
                                         checkable=True,
                                         statusTip="Show running middle of current signal value")
        self.action_viewas_eff = QAction(QIcon(),
                                         "&Eff",
                                         self,
                                         checkable=True,
                                         statusTip="Show RMS of current signal value")
        self.action_viewas_hrm1 = QAction(QIcon(),
                                          "Hrm &1",
                                          self,
                                          checkable=True,
                                          statusTip="Show harmonic #1 of signal value")
        self.action_viewas_hrm2 = QAction(QIcon(),
                                          "Hrm &2",
                                          self,
                                          checkable=True,
                                          statusTip="Show harmonic #2 of signal value")
        self.action_viewas_hrm3 = QAction(QIcon(),
                                          "Hrm &3",
                                          self,
                                          checkable=True,
                                          statusTip="Show harmonic #3 of signal value")
        self.action_viewas_hrm5 = QAction(QIcon(),
                                          "Hrm &5",
                                          self,
                                          checkable=True,
                                          statusTip="Show harmonic #5 of signal value")
        self.action_ptr_add_tmp = QAction(QIcon(),
                                          "Add temporary pointer",
                                          self,
                                          statusTip="Add temporary pointer into current position",
                                          triggered=self.__do_ptr_add_tmp)
        self.action_ptr_add_msr = QAction(QIcon(),
                                          "Add measure pointers",
                                          self,
                                          statusTip="Add measure pointers into current position",
                                          triggered=self.__do_ptr_add_msr)
        self.action_ptr_add_lvl = QAction(QIcon(),
                                          "Add level pointers",
                                          self,
                                          statusTip="Add level pointers into current position",
                                          triggered=self.__do_ptr_add_lvl)
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

    def __mk_menu(self):
        menu_file = self.menubar.addMenu("&File")
        menu_file.addAction(self.action_info)
        menu_file.addAction(self.action_convert)
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
        menu_channel = self.menubar.addMenu("&Channel")
        menu_channel.addAction(self.action_unhide)
        menu_ptr = self.menubar.addMenu("&Pointers")
        menu_ptr.addAction(self.action_ptr_add_tmp)
        menu_ptr.addAction(self.action_ptr_add_msr)
        menu_ptr.addAction(self.action_ptr_add_lvl)

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
        self.xscroll_bar.signal_update_plots.connect(self.timeaxis_bar.plot.slot_rerange)

    def __set_data(self):
        for sig in self.osc.y:
            ss = SignalSuit(sig, self)
            if not sig.is_bool:
                self.analog_table.bar_insert().sig_add(ss)  # FIXME: default height
            else:
                self.status_table.bar_insert().sig_add(ss)  # FIXME: default height

    def __do_file_close(self):  # FIXME: not closes tab
        # self.parent().removeTab(self.__index)
        self.close()

    def __do_file_info(self):
        def tr(name: str, value: Any):
            return f"<tr><th>{name}:</th><td>{value}</td></tr>"

        msg = QMessageBox(QMessageBox.Icon.Information, "Comtrade file info", "Summary")
        # plan A:
        # msg.setDetailedText(self.osc.cfg_summary())
        # plan B
        txt = "<html><body><table><tbody>"
        txt += tr("File", self.__path)  # was self.osc.raw.cfg.filepath
        txt += tr("Station name", self.osc.raw.station_name)
        txt += tr("Station id", self.osc.raw.rec_dev_id)
        txt += tr("Comtrade ver.", self.osc.raw.rev_year)
        txt += tr("File format", self.osc.raw.ft)
        txt += tr("Analog chs.", self.osc.raw.analog_count)
        txt += tr("Status chs.", self.osc.raw.status_count)
        txt += tr("Line freq, Hz", self.osc.raw.frequency)
        txt += tr("Time", f"{self.osc.raw.start_timestamp}&hellip;{self.osc.raw.trigger_timestamp}"
                          f" with &times; {self.osc.raw.cfg.timemult}")
        txt += tr("Time base", self.osc.raw.time_base)
        txt += tr("Samples", self.osc.raw.total_samples)
        for i in range(len(self.osc.rate)):
            rate, points = self.osc.rate[i]
            txt += tr(f"Sample #{i + 1}", f"{points} points at {rate} Hz")
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

    def __do_unhide(self):
        self.signal_unhide_all.emit()

    def __do_ysize_all_in(self):
        self.signal_ysize_all_in.emit()

    def __do_ysize_all_out(self):
        self.signal_ysize_all_out.emit()

    def __update_xzoom_actions(self):
        """Set X-zoom actions availability"""
        self.action_zoom_x_in.setEnabled(self.x_zoom > 0)
        self.action_zoom_x_out.setEnabled(self.x_zoom < (len(iosc.const.X_PX_WIDTH_uS) - 1))

    def __do_xzoom(self, dxz: int = 0):
        if 0 <= self.x_zoom + dxz < len(iosc.const.X_PX_WIDTH_uS):
            self.x_zoom += dxz
            self.__update_xzoom_actions()
            self.signal_x_zoom.emit()

    def __do_xzoom_in(self):
        self.__do_xzoom(-1)

    def __do_xzoom_out(self):
        self.__do_xzoom(1)

    def __do_shift(self, _: QAction):
        self.osc.shifted = self.action_shift_yes.isChecked()
        self.signal_chged_shift.emit()

    def __do_pors(self, _: QAction):
        self.show_sec = self.action_pors_sec.isChecked()
        self.signal_chged_pors.emit()

    def __do_viewas(self, a: QAction):
        self.viewas = a.data()
        self.viewas_toolbutton.setDefaultAction(a)
        self.signal_chged_func.emit()

    def __do_ptr_add_tmp(self):
        uid = max(self.__tmp_ptr_i.keys()) + 1 if self.__tmp_ptr_i.keys() else 1  # generate new uid
        self.__tmp_ptr_i[uid] = self.__main_ptr_i
        self.signal_ptr_add_tmp.emit(uid)  # create them ...
        # self.slot_ptr_moved_tmp(uid, self.__main_ptr_i)  # ... and __move

    def __do_ptr_add_msr(self):
        if sig_selected := SelectSignalsDialog(self.osc.y).execute():
            for i in sig_selected:
                uid = max(self.msr_ptr_uids) + 1 if self.msr_ptr_uids else 1
                self.sig_no2widget[0][i].add_ptr_msr(uid, self.main_ptr_i)

    def __do_ptr_add_lvl(self):
        if sig_selected := SelectSignalsDialog(self.osc.y).execute():
            for i in sig_selected:
                uid = max(self.lvl_ptr_uids) + 1 if self.lvl_ptr_uids else 1
                self.sig_no2widget[0][i].add_ptr_lvl(uid)

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
        name = self.timeaxis_bar.widget.get_tmp_ptr_name(uid)
        form = TmpPtrDialog((v, self.x_min(), self.x_max(), self.x_step(), name))
        if form.exec_():
            self.timeaxis_bar.widget.set_tmp_ptr_name(uid, form.f_name.text())
            self.signal_ptr_moved_tmp.emit(uid, self.x2i(form.f_val.value()))

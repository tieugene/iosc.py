"""Signal tab widget
RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import pathlib
from typing import Any, Optional

# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget, QMenuBar, QToolBar, QAction, QMessageBox, \
    QFileDialog, QHBoxLayout, QActionGroup, QToolButton, QMenu
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.icon import svg_icon, ESvgSrc
from iosc.core.convtrade import convert, ConvertError
from iosc.sig.section import TimeAxisTable, SignalListTable, StatusBarTable, HScroller

# x. const
TICK_RANGE = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000)
TICS_PER_CHART = 20


def find_std_ti(ti: int):
    for i in TICK_RANGE:
        if i >= ti:
            return i
    return TICK_RANGE[-1]


class ComtradeWidget(QWidget):
    """
    Main osc window. Includes analog and status panels
    """
    # inner cons
    __osc: mycomtrade.MyComtrade
    __tpp: int  # tics (samples) per signal period
    # inner vars
    __mptr: int  # current Main Ptr index in source arrays
    __shifted: bool  # original/shifted selector
    __chart_width: Optional[int]  # width (px) of nested QCP charts
    __xzoom: int
    show_sec: bool  # pri/sec selector
    viewas: int  # TODO: enum
    # actions
    action_close: QAction
    action_info: QAction
    action_convert: QAction
    action_vzoom_in: QAction
    action_vzoom_out: QAction
    action_xzoom_in: QAction
    action_xzoom_out: QAction
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
    # widgets
    menubar: QMenuBar
    toolbar: QToolBar
    viewas_toolbutton: QToolButton
    timeaxis_table: TimeAxisTable
    analog_table: SignalListTable
    status_table: SignalListTable
    statusbar_table: StatusBarTable
    hsb: HScroller  # bottom horizontal scroll bar
    # signals
    signal_main_ptr_moved = pyqtSignal()  # refresh Signal(Ctrl/Chart)View on MainPtr moved
    signal_recalc_achannels = pyqtSignal()  # recalc ASignalCtrlView on ...
    signal_shift_achannels = pyqtSignal()  # refresh ASignal*View on switching original/shifted
    signal_xscale = pyqtSignal(int, int)  # set signal chart widths

    def __init__(self, rec: mycomtrade.MyComtrade, parent: QTabWidget):
        super().__init__(parent)
        self.__osc = rec
        self.__tpp = round(self.__osc.raw.cfg.sample_rates[0][0] / self.__osc.raw.cfg.frequency)
        self.__mptr = self.__x2n(0)
        self.__shifted = False
        self.__chart_width = None  # wait for line_up
        self.__xzoom = 1
        self.show_sec = True
        self.viewas = 0
        ti_wanted = int(self.__osc.raw.total_samples * (1000 / self.__osc.rate[0][0]) / TICS_PER_CHART)  # ms
        ti = find_std_ti(ti_wanted)
        # print(f"{ti_wanted} => {ti}")
        self.__mk_widgets()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_toolbar()
        self.__mk_layout()
        self.__mk_connections()
        # sync: default z-point
        # self.signal_main_ptr_moved.emit()

    @property
    def tpp(self) -> int:
        return self.__tpp

    @property
    def mptr(self) -> int:
        return self.__mptr

    @property
    def shifted(self):
        return self.__osc.shifted

    @property
    def chart_width(self):
        return self.__chart_width * self.__xzoom if self.__chart_width is not None else None

    @property
    def xzoom(self):
        return self.__xzoom

    @property
    def mptr_x(self) -> float:
        return 1000 * (self.__osc.raw.time[self.__mptr] - self.__osc.raw.trigger_time)

    def __x2n(self, x: float) -> int:
        """Recalc graph x-position into index in signal array"""
        return int(round((self.__osc.raw.trigger_time + x / 1000) * self.__osc.rate[0][0]))

    def __mk_widgets(self):
        self.menubar = QMenuBar()
        self.toolbar = QToolBar(self)
        self.viewas_toolbutton = QToolButton(self)
        self.hsb = HScroller(self)
        self.timeaxis_table = TimeAxisTable(self.__osc, self)
        self.analog_table = SignalListTable(self.__osc.analog, self)
        self.status_table = SignalListTable(self.__osc.status, self)
        self.statusbar_table = StatusBarTable(self.__osc, self)

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
        self.action_vzoom_in = QAction(svg_icon(ESvgSrc.VZoomIn),
                                       "Y-Zoom &in",
                                       self,
                                       statusTip="Vertical zoom in all",
                                       triggered=self.__do_vzoom_in)
        self.action_vzoom_out = QAction(svg_icon(ESvgSrc.VZoomOut),
                                        "Y-Zoom &out",
                                        self,
                                        statusTip="Vertical zoom out all",
                                        triggered=self.__do_vzoom_out)
        self.action_xzoom_in = QAction(svg_icon(ESvgSrc.HZoomIn),
                                       "X-Zoom in",
                                       self,
                                       statusTip="Horizontal zoom in all",
                                       triggered=self.__do_xzoom_in)
        self.action_xzoom_out = QAction(svg_icon(ESvgSrc.HZoomOut),
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
        self.action_xzoom_out.setEnabled(False)

    def __mk_menu(self):
        menu_file = self.menubar.addMenu("&File")
        menu_file.addAction(self.action_info)
        menu_file.addAction(self.action_convert)
        menu_file.addAction(self.action_close)
        menu_view = self.menubar.addMenu("&View")
        menu_view.addAction(self.action_vzoom_in)
        menu_view.addAction(self.action_vzoom_out)
        menu_view.addAction(self.action_xzoom_in)
        menu_view.addAction(self.action_xzoom_out)
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

    def __mk_toolbar(self):
        # prepare
        self.viewas_toolbutton.setPopupMode(QToolButton.MenuButtonPopup)
        viewas_menu = QMenu()
        viewas_menu.addActions(self.action_viewas.actions())
        self.viewas_toolbutton.setMenu(viewas_menu)
        self.viewas_toolbutton.setDefaultAction(self.action_viewas.actions()[self.viewas])
        # go
        self.toolbar.addAction(self.action_vzoom_in)
        self.toolbar.addAction(self.action_vzoom_out)
        self.toolbar.addAction(self.action_xzoom_in)
        self.toolbar.addAction(self.action_xzoom_out)
        self.toolbar.addAction(self.action_shift_not)
        self.toolbar.addAction(self.action_shift_yes)
        self.toolbar.addAction(self.action_pors_pri)
        self.toolbar.addAction(self.action_pors_sec)
        self.toolbar.addWidget(self.viewas_toolbutton)
        self.toolbar.addAction(self.action_info)

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
        self.layout().addWidget(self.timeaxis_table)
        # 3. 2 x signal tables
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.analog_table)
        splitter.addWidget(self.status_table)
        self.layout().addWidget(splitter)
        # 4. bottom status bar
        self.layout().addWidget(self.statusbar_table)
        # 5. bottom scrollbar
        self.layout().addWidget(self.hsb)

    def __mk_connections(self):
        self.action_shift.triggered.connect(self.__do_shift)
        self.action_pors.triggered.connect(self.__do_pors)
        self.action_viewas.triggered.connect(self.__do_viewas)
        self.timeaxis_table.horizontalHeader().sectionResized.connect(self.__sync_hresize)

    def __do_file_close(self):  # FIXME: not closes tab
        # self.parent().removeTab(self.__index)
        self.close()

    def __do_file_info(self):
        def tr(name: str, value: Any):
            return f"<tr><th>{name}:</th><td>{value}</td></tr>"

        msg = QMessageBox(QMessageBox.Icon.Information, "Comtrade file info", "Summary")
        # plan A:
        # msg.setDetailedText(self.__osc.cfg_summary())
        # plan B
        txt = "<html><body><table><tbody>"
        txt += tr("File", self.__osc.raw.cfg.filepath)
        txt += tr("Station name", self.__osc.raw.station_name)
        txt += tr("Station id", self.__osc.raw.rec_dev_id)
        txt += tr("Comtrade ver.", self.__osc.raw.rev_year)
        txt += tr("File format", self.__osc.raw.ft)
        txt += tr("Analog chs.", len(self.__osc.analog))
        txt += tr("Status chs.", len(self.__osc.status))
        txt += tr("Line freq, Hz", self.__osc.raw.frequency)
        txt += tr("Time", f"{self.__osc.raw.start_timestamp}&hellip;{self.__osc.raw.trigger_timestamp}"
                          f" with &times; {self.__osc.raw.cfg.timemult}")
        txt += tr("Time base", self.__osc.raw.time_base)
        txt += tr("Samples", self.__osc.raw.total_samples)
        for i in range(len(self.__osc.rate)):
            rate, points = self.__osc.rate[i]
            txt += tr(f"Sample #{i + 1}", f"{points} points at {rate} Hz")
        txt += "<tbody></table></body><html>"
        msg.setText(txt)
        msg.setTextFormat(Qt.RichText)
        # # /plan
        msg.exec_()

    def __do_file_convert(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Save file as %s" % {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[self.__osc.raw.ft]
        )
        if fn[0]:
            try:
                convert(pathlib.Path(self.__osc.raw.cfg.filepath), pathlib.Path(fn[0]))
            except ConvertError as e:
                QMessageBox.critical(self, "Converting error", str(e))

    def __do_unhide(self):
        self.analog_table.slot_unhide()
        self.status_table.slot_unhide()

    def __do_vzoom_in(self):
        self.analog_table.slot_vzoom_in()
        self.status_table.slot_vzoom_in()

    def __do_vzoom_out(self):
        self.analog_table.slot_vzoom_out()
        self.status_table.slot_vzoom_out()

    def __do_xzoom_in(self):
        samples = len(self.__osc.raw.time)
        if int(self.__chart_width * (zoom_new := self.__xzoom << 1) / samples) <= iosc.const.X_SCATTER_MAX:
            if not self.action_xzoom_out.isEnabled():
                self.action_xzoom_out.setEnabled(True)
            if int(self.__chart_width * (zoom_new << 1) / samples) > iosc.const.X_SCATTER_MAX:
                self.action_xzoom_in.setEnabled(False)
            chart_width_old = self.chart_width
            self.__xzoom = zoom_new
            self.signal_xscale.emit(chart_width_old, self.chart_width)

    def __do_xzoom_out(self):
        if self.__xzoom > 1:
            if self.__xzoom == 2:
                self.action_xzoom_out.setEnabled(False)
            if not self.action_xzoom_in.isEnabled():  # TODO: not
                self.action_xzoom_in.setEnabled(True)
            chart_width_old = self.chart_width
            self.__xzoom >>= 1
            self.signal_xscale.emit(chart_width_old, self.chart_width)

    def __do_shift(self, _: QAction):
        self.__osc.shifted = self.action_shift_yes.isChecked()
        self.signal_shift_achannels.emit()

    def __do_pors(self, _: QAction):
        self.show_sec = self.action_pors_sec.isChecked()
        self.signal_recalc_achannels.emit()

    def __do_viewas(self, a: QAction):
        self.viewas = a.data()
        self.viewas_toolbutton.setDefaultAction(a)
        self.signal_recalc_achannels.emit()

    def __sync_hresize(self, l_index: int, old_size: int, new_size: int):
        """
        :param l_index: Column index
        :param old_size: Old size
        :param new_size: New size
        :todo: remake to signal/slot
        """
        # self.timeaxis_table.horizontalHeader().resizeSection(l_index, new_size)  # don't touch itself
        self.analog_table.horizontalHeader().resizeSection(l_index, new_size)
        self.status_table.horizontalHeader().resizeSection(l_index, new_size)
        self.statusbar_table.horizontalHeader().resizeSection(l_index, new_size)
        if l_index == 1:  # it is chart column
            self.hsb.slot_col_resize(old_size, new_size)

    def line_up(self):
        """
        Initial line up table colums (and rows further) according to requirements and actual geometry.
        """
        w_main_avail = QGuiApplication.screens()[0].availableGeometry().width()  # all available desktop (e.g. 1280)
        w_main_real = QGuiApplication.topLevelWindows()[0].width()  # current main window width (e.g. 960)
        w_self = self.analog_table.width()  # current [table] widget width  (e.g. 940)
        self.__chart_width = w_self + (w_main_avail - w_main_real) - iosc.const.COL0_WIDTH  # - const.MAGIC_WIDHT
        self.signal_xscale.emit(0, self.chart_width)

    def slot_main_ptr_moved_x(self, x: float):
        """
        Dispatch all main ptrs
        :param x: New Main Ptr x-position
        :type x: ~~QCPItemPosition~~ float
        Emit slot_main_ptr_move(pos) for:
        - TimeAxisWidget (x)
        - SignalChartWidget (x) [=> SignalCtrlWidget(y)]
        - statusbar (x)
        """
        self.__mptr = self.__x2n(x)
        self.signal_main_ptr_moved.emit()

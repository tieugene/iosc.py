"""Signal tab widget
RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import pathlib
from typing import Any, Dict
# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMenuBar, QToolBar, QAction, QMessageBox, \
    QFileDialog, QHBoxLayout, QActionGroup, QToolButton, QMenu
# 3. local
import iosc.const
from iosc.core import mycomtrade
from iosc.icon import svg_icon, ESvgSrc
from iosc.core.convtrade import convert, ConvertError
from iosc.sig.cvd.cvdwindow import CVDWindow
from iosc.sig.section import TimeAxisBar, SignalBarTable, TimeStampsBar, XScroller
from iosc.sig.widget.common import AnalogSignalSuit, StatusSignalSuit
from iosc.sig.widget.dialog import TmpPtrDialog, SelectSignalsDialog


class ComtradeWidget(QWidget):
    """Main osc window."""
    # inner cons
    osc: mycomtrade.MyComtrade
    col_ctrl_width: int
    # inner vars
    __main_ptr_i: int  # current Main Ptr index in source arrays
    __sc_ptr_i: int  # current OMP SC Ptr index in source arrays
    __tmp_ptr_i: dict[int, int]  # current Tmp Ptr indexes in source arrays: ptr_uid => x_idx
    msr_ptr_uids: set[int]  # MsrPtr uids
    lvl_ptr_uids: set[int]  # LvlPtr uids
    __omp_width: int  # distance from OMP PR and SC pointers, periods
    __shifted: bool  # original/shifted selector
    x_zoom: int
    show_sec: bool  # pri/sec selector
    viewas: int  # TODO: enum
    ass_list: list[AnalogSignalSuit]  # Translate signal no to chart widget
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
    action_vector_diagram: QAction
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

    def __init__(self, osc: mycomtrade.MyComtrade, parent: 'ComtradeTabWidget'):
        super().__init__(parent)
        self.osc = osc
        self.col_ctrl_width = iosc.const.COL0_WIDTH_INIT
        self.__main_ptr_i = self.x2i(0.0)  # default: Z (Osc1: 600)
        self.__sc_ptr_i = self.__main_ptr_i + 2 * self.osc.spp
        self.__tmp_ptr_i = dict()
        self.msr_ptr_uids = set()
        self.lvl_ptr_uids = set()
        self.__omp_width = 3
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

    # property
    def x_width_px(self) -> int:
        return round(self.osc.x_size * 1000 / iosc.const.X_PX_WIDTH_uS[self.x_zoom])

    # property
    def x_sample_width_px(self) -> int:
        """Current width of samples interval in px"""
        return round(self.x_width_px() / self.osc.raw.total_samples)

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
        menu_tools = self.menubar.addMenu("&Tools")
        menu_tools.addAction(self.action_vector_diagram)

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

    def __do_file_close(self):  # FIXME: not closes tab
        # self.close()  # close widget but not tab itself
        self.parent().parent().removeTab(self.parent().indexOf(self))  # QStackedWidget.ComtradeTabWidget

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

    def __do_unhide(self):
        self.signal_unhide_all.emit()

    def __do_resize_y_all_inc(self):
        self.analog_table.resize_y_all(True)
        self.status_table.resize_y_all(True)

    def __do_resize_y_all_dec(self):
        self.analog_table.resize_y_all(False)
        self.status_table.resize_y_all(False)

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
        CVDWindow(self).show()

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

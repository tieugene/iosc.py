"""Signal tab widget
RTFM context menu: examples/webenginewidgets/tabbedbrowser
"""
import pathlib
from typing import Any

# 2. 3rd
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget, QMenuBar, QToolBar, QAction, QMessageBox, \
    QFileDialog, QHBoxLayout, QActionGroup
# 3. local
import mycomtrade
from convtrade import convert, ConvertError
from siglist_tw import AnalogSignalListView, StatusSignalListView
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
    __osc: mycomtrade.MyComtrade
    action_close: QAction
    action_info: QAction
    action_convert: QAction
    action_unhide: QAction
    action_pors: QActionGroup
    action_pors_pri: QAction
    action_pors_sec: QAction
    menubar: QMenuBar
    toolbar: QToolBar
    analog_table: AnalogSignalListView
    status_table: StatusSignalListView
    signal_main_ptr_moved_x = pyqtSignal(float)
    show_sec: bool

    def __init__(self, rec: mycomtrade.MyComtrade, parent: QTabWidget):
        super().__init__(parent)
        self.__osc = rec
        self.show_sec = True
        ti_wanted = int(self.__osc.raw.total_samples * (1000 / self.__osc.rate[0][0]) / TICS_PER_CHART)  # ms
        ti = find_std_ti(ti_wanted)
        # print(f"{ti_wanted} => {ti}")
        self.__mk_widgets(ti)
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_toolbar()
        self.__mk_layout()
        self.__mk_connections()
        # sync
        self.signal_main_ptr_moved_x.emit(0)

    def __mk_widgets(self, ti):
        self.menubar = QMenuBar()
        self.toolbar = QToolBar(self)
        self.analog_table = AnalogSignalListView(self.__osc.analog, ti, self)
        self.status_table = StatusSignalListView(self.__osc.status, ti, self)

    def __mk_actions(self):
        self.action_close = QAction(QIcon.fromTheme("window-close"),  # TODO: disable if nobodu
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
        self.action_unhide = QAction(QIcon.fromTheme("edit-undo"),
                                       "&Unhide all",
                                       self,
                                       statusTip="Show hidden channels",
                                       triggered=self.__do_unhide)
        self.action_pors_pri = QAction(QIcon(),
                                       "&Primary",
                                       self,
                                       checkable=True,
                                       statusTip="Show primary signal value",
                                       triggered=self.__do_pors_pri)
        self.action_pors_sec = QAction(QIcon(),
                                       "&Secondary",
                                       self,
                                       checkable=True,
                                       statusTip="Show secondary signal values",
                                       triggered=self.__do_pors_sec)
        self.action_pors = QActionGroup(self)
        self.action_pors.addAction(self.action_pors_pri)
        self.action_pors.addAction(self.action_pors_sec)
        if self.show_sec:
            self.action_pors_sec.setChecked(True)
        else:
            self.action_pors_pri.setChecked(True)

    def __mk_menu(self):
        menu_file = self.menubar.addMenu("&File")
        menu_file.addAction(self.action_info)
        menu_file.addAction(self.action_convert)
        menu_file.addAction(self.action_close)
        menu_channel = self.menubar.addMenu("&Channel")
        menu_channel.addSeparator().setText("Pri/Sec")
        menu_channel.addAction(self.action_pors_pri)
        menu_channel.addAction(self.action_pors_sec)
        menu_channel.addSeparator()
        menu_channel.addAction(self.action_unhide)

    def __mk_toolbar(self):
        self.toolbar.addAction(self.action_pors_pri)
        self.toolbar.addAction(self.action_pors_sec)
        self.toolbar.addAction(self.action_info)

    def __mk_layout(self):
        self.setLayout(QVBoxLayout())
        topbar = QWidget()
        topbar.setLayout(QHBoxLayout())
        topbar.layout().addWidget(self.menubar)
        topbar.layout().addWidget(self.toolbar)
        self.layout().addWidget(topbar)
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet("QSplitter::handle{background: grey;}")
        splitter.addWidget(self.analog_table)
        splitter.addWidget(self.status_table)
        self.layout().addWidget(splitter)

    def __mk_connections(self):
        self.analog_table.horizontalScrollBar().valueChanged.connect(self.__sync_hscrolls)
        self.status_table.horizontalScrollBar().valueChanged.connect(self.__sync_hscrolls)
        self.analog_table.horizontalHeader().sectionResized.connect(self.__sync_hresize)
        self.status_table.horizontalHeader().sectionResized.connect(self.__sync_hresize)

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
        fn = QFileDialog.getSaveFileName(self, "Save file as %s" % {'ASCII': 'BINARY', 'BINARY': 'ASCII'}[self.__osc.raw.ft])
        if fn[0]:
            try:
                convert(pathlib.Path(self.__osc.raw.filepath), pathlib.Path(fn[0]))
            except ConvertError as e:
                QMessageBox.critical(self, "Converting error", str(e))

    def __do_unhide(self):
        self.analog_table.sig_unhide()
        self.status_table.sig_unhide()

    def __do_pors_pri(self):
        self.show_sec = False

    def __do_pors_sec(self):
        self.show_sec = True

    def __sync_hscrolls(self, index):
        self.analog_table.horizontalScrollBar().setValue(index)
        self.status_table.horizontalScrollBar().setValue(index)

    def __sync_hresize(self, l_index: int, _: int, new_size: int):
        """
        :param l_index: Column index
        :param _: Old size
        :param new_size: New size
        :return:
        """
        self.analog_table.horizontalHeader().resizeSection(l_index, new_size)
        self.status_table.horizontalHeader().resizeSection(l_index, new_size)

    def line_up(self, dwidth: int):
        """
        Line up table colums (and rows further) according to requirements and actual geometry.
        :param dwidth: Main window widths subtraction (available - actual)
        """
        self.analog_table.line_up(dwidth)
        self.status_table.line_up(dwidth)

    def slot_main_ptr_moved_x(self, x: float):
        """
        :param x:
        :type x: ~~QCPItemPosition~~ float
        Emit slot_main_ptr_move(pos) for:
        - TimeAxisView (x)
        - SignalChartView (x) [=> SignalCtrlView(y)]
        - statusbar (x)
        """
        # print("You win")
        self.signal_main_ptr_moved_x.emit(x)

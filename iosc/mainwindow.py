"""Main application Window."""
import json
# 1. std
import pathlib
import sys

# 2. 3rd
from PyQt5.QtCore import Qt, QCoreApplication, QTranslator, QLocale
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QAction, QFileDialog, QToolBar, QWidget, QHBoxLayout, QApplication
# 3. local
import iosc.const
from iosc._version import __version__
from iosc.maintabber import ComtradeTabWidget, MAIN_TAB
import iosc.qrc
from iosc.dialog import OMPSaveDialog

# from iosc.prefs import AppSettingsDialog, load_style  #275: Styling off

# x. const
MAIN_MENU = True  # FIXME: False => hot keys not work
OMP_KEYS = (
    ('uassc', 'ubssc', 'ucssc', 'iassc', 'ibssc', 'icssc', 'uaspr', 'iaspr'),
    ('uarsc', 'ubrsc', 'ucrsc', 'iarsc', 'ibrsc', 'icrsc', 'uarpr', 'iarpr'),
)


# SHARES_DIR: pathlib.PosixPath  # 277: i18n2qrc


class MainWindow(QMainWindow):
    """Main application window."""

    tabs: ComtradeTabWidget
    act_bar: QToolBar
    dlg_omp: OMPSaveDialog
    act_file_open: QAction
    act_omp_save: QAction
    # act_settings: QAction  #275: Styling off
    act_exit: QAction
    act_about: QAction

    # __settings: QSettings  #275: Styling off

    def __init__(self, _: list):
        """Init MainWindow object."""
        super().__init__()
        # self.__settings = QSettings()  #275: Styling off
        # load_style(self.__settings, SHARES_DIR)  #275: Styling off
        self.__mk_widgets()
        self.__mk_actions()
        self.__mk_menu()
        self.__mk_layout()
        self.setWindowTitle("iOsc")
        # self.handle_cli()

    def __mk_widgets(self):
        """Create child widgets."""
        self.tabs = ComtradeTabWidget(self)
        self.dlg_omp = OMPSaveDialog(self)
        self.setCentralWidget(self.tabs)
        # self.act_bar = QToolBar(self)

    def __mk_actions(self):
        """Create qctions required."""
        # noinspection PyArgumentList
        self.act_file_open = QAction(QIcon.fromTheme("document-open"),
                                     self.tr("&Open"),
                                     self,
                                     shortcut="Ctrl+O",
                                     statusTip=self.tr("Load comtrade file"),
                                     triggered=self.__do_file_open)
        # noinspection PyArgumentList
        # 275: Styling off
        # self.act_settings = QAction(QIcon.fromTheme("preferences-system"),
        #                            self.tr("&Settings"),
        #                            self,
        #                            statusTip=self.tr("Settings"),
        #                            triggered=self.__do_settings)
        # noinspection PyArgumentList
        self.act_omp_save = QAction(self.tr("OMP map save"),
                                    self,
                                    triggered=self.__do_omp_save)
        # noinspection PyArgumentList
        self.act_exit = QAction(QIcon.fromTheme("application-exit"),
                                self.tr("E&xit"),
                                self,
                                shortcut="Ctrl+Q",
                                statusTip=self.tr("Exit the application"),
                                triggered=self.close)
        # noinspection PyArgumentList
        self.act_about = QAction(QIcon.fromTheme("help-about"),
                                 self.tr("&About"),
                                 self,
                                 statusTip=self.tr("Show the application's 'About' box"),
                                 triggered=self.__do_about)

    def __mk_menu(self):
        """Create main application menu."""
        self.menuBar().addMenu(self.tr("&File")).addActions((
            self.act_file_open,
            self.act_omp_save,
            # self.act_settings,  #275: Styling off
            self.act_exit
        ))
        self.menuBar().addMenu(self.tr("&Help")).addAction(self.act_about)
        self.menuBar().setVisible(MAIN_MENU)

    def __mk_layout(self):
        """Lay out child widgets."""
        main_tab = QWidget()
        main_tab.setLayout(QHBoxLayout())
        # main_tab.layout().addWidget(self.act_bar)
        main_tab.layout().addWidget(QWidget())
        if MAIN_TAB:
            self.tabs.addTab(main_tab, self.tr("File"))

    def handle_cli(self):
        """Process CLI arg."""
        argv = QCoreApplication.arguments()
        if len(argv) > 2:
            QMessageBox.warning(self, self.tr("CLI error"), self.tr("One file only"))
        elif len(argv) == 2:
            file = pathlib.Path(argv[1])
            if not file.is_file():
                QMessageBox.warning(self, self.tr("CLI error"), self.tr("'%s' not exists or is not file") % file)
            else:
                self.tabs.add_chart_tab(file)

    def __do_file_open(self):
        """Open comtrade file."""
        fn = QFileDialog.getOpenFileName(
            self,
            self.tr("Open data"),
            "",
            self.tr("Comtrade Files (*.cfg *.cff)")
        )
        if fn[0]:
            self.tabs.add_chart_tab(pathlib.Path(fn[0]))

    def __do_omp_save(self):
        """
        - Collect lefts, rights, boths
        - Prepare x4 listboxes
        - call select s/r dialog
        - call QFileDialog
        - do it
        :return:
        """
        # 1. Collect lefts|rights
        if self.tabs.count() < 1:  # no one osc loaded
            return
        if not (ct_list := [
            ct for i in range(self.tabs.count())
            if (ct := self.tabs.widget(i)).ompmapwin and ct.ompmapwin.is_defined
        ]):
            return  # no one OMP map defined
        # 2. Select oscs
        if not (sr := self.dlg_omp.execute(ct_list)):
            return  # nothing selected
        # 3. Call file dialog
        fn = QFileDialog.getSaveFileName(
            self,
            self.tr("Save OMP values"),
            '',
            self.tr("U,I measurements (*.uim)")
        )
        # 4. Save
        if fn[0]:
            # - prepare data
            raw_data = [
                [complex(0, 0)] * 8 if sr[i] is None else ct_list[sr[i]].ompmapwin.data(i)
                for i in range(2)
            ]
            # - fill out
            out_data = {}
            for i, side in enumerate(OMP_KEYS):
                for j, key in enumerate(side):
                    out_data[key + 'r'] = raw_data[i][j].real
                    out_data[key + 'i'] = raw_data[i][j].imag
            # - saving itself
            with open(fn[0], 'wt') as fp:
                json.dump(out_data, fp, indent=1)
            # self.ompmapwin.data_save(pathlib.Path(fn[0]))

    # def __do_settings(self):  #275: Styling off
    #    dialog = AppSettingsDialog(self.__settings, SHARES_DIR, self)
    #    dialog.execute()

    # actions
    def __do_about(self):
        """Show 'About' message box."""
        # QMessageBox.about(self, "About iOsc.py", ABOUT_STR)
        dialog = QMessageBox(
            QMessageBox.Information,
            self.tr("About iOsc"),
            self.tr("Comtrade files viewing/analyzing software, version %s<br/>") % __version__ +
            self.tr('Developed for <a href="https://ntkpribor.ru/">&laquo;NTK Priborenergo&raquo;, Ltd.</a><br/>') +
            '<sub>&copy; <a href="https://www.eap.su">TI_Eugene</a></sub>',
            QMessageBox.Ok,
            self
        )
        dialog.setTextFormat(Qt.RichText)
        dialog.exec_()


def main():
    """Application entry point."""
    # global SHARES_DIR  # 277: i18n2qrc
    # QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    # app.setOrganizationName('TI_Eugene')
    app.setOrganizationDomain('eap.su')
    app.setApplicationName('iosc')
    app.setApplicationVersion(__version__)
    # <setup data path>
    # if (i18n_dir := pathlib.Path(__file__).resolve().parent.joinpath(iosc.const.i18N_DIR)).exists():
    #    ...
    # elif i18n_dir := QStandardPaths.locate(
    #        QStandardPaths.DataLocation,
    #        iosc.const.i18N_DIR,
    #        QStandardPaths.LocateDirectory):
    #    i18n_dir = pathlib.PosixPath(i18n_dir)
    # else:
    #    sys.exit(1)
    # SHARES_DIR = i18n_dir.parent  # 277: i18n2qrc
    # </setup ...>
    translator = QTranslator()
    # if translator.load(QLocale(), 'iosc', '_', SHARES_DIR.joinpath(iosc.const.i18N_DIR).as_posix()):
    if translator.load(QLocale(), 'iosc', '_', f":{iosc.const.i18N_DIR}"):
        app.installTranslator(translator)
    mw: MainWindow = MainWindow(sys.argv)
    available_geometry = app.desktop().availableGeometry(mw)  # 0, 0, 1280, 768 (display height - taskbar)
    mw.resize(int(available_geometry.width() * 3 / 4), int(available_geometry.height() * 3 / 4))
    mw.show()
    mw.handle_cli()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

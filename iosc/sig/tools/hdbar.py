# 2. 3rd
from PyQt5.QtCore import QMargins
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame, QVBoxLayout
# 3. locals
from iosc.sig.tools.util import color2style
from iosc.sig.widget.common import AnalogSignalSuit
# x. const
FONT_STD = QFont('mono', 8)
WIDTH_HRM_TITLE = 70
WIDTH_HRM_LEGEND = 35


class SignalHarmBar(QWidget):
    class _Text(QWidget):
        subj: QLabel

        def __init__(self, parent: 'SignalHarmBar'):
            super().__init__(parent)
            self.subj = QLabel(self)
            self.subj.setFont(FONT_STD)
            self.setLayout(QHBoxLayout())
            self.layout().setContentsMargins(QMargins())
            self.layout().setSpacing(0)
            self.layout().addWidget(self.subj)

        def set_text(self, text: str):
            self.subj.setText(text)

    class _Space(QFrame):
        def __init__(self, parent: 'SignalHarmBar'):
            super().__init__(parent)

        def set_color(self, color: QColor):
            self.setStyleSheet("background-color: %s" % color2style(color))

    h_no: int
    title: _Text
    indic: _Space
    legend: _Text
    pad: _Space
    """One harmonic row"""
    def __init__(self, h_no: int, parent: 'HDBar'):
        """
        :param h_no: Harmonic number
        :param parent: Subj
        """
        super().__init__(parent)
        self.h_no = h_no
        # self.setStyleSheet("border: 1px dotted black")
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(QMargins())
        self.layout().setSpacing(0)
        # 1. mk widgets
        # - title
        self.title = self._Text(self)
        self.title.setFixedWidth(WIDTH_HRM_TITLE)
        self.title.set_text(f"{h_no}: {h_no * 50} Гц")  # FIXME: use ss.signal.frequency
        self.layout().addWidget(self.title)
        self.layout().setStretchFactor(self.title, 0)
        # - indicator
        self.indic = self._Space(self)
        self.layout().addWidget(self.indic)
        # - percentage
        self.legend = self._Text(self)
        self.legend.setFixedWidth(WIDTH_HRM_LEGEND)
        self.layout().addWidget(self.legend)
        self.layout().setStretchFactor(self.legend, 0)
        # - pad
        self.pad = self._Space(self)
        self.layout().addWidget(self.pad)

    def set_value(self, v: int, v_max: int):
        self.legend.set_text(f"{v}%")
        self.layout().setStretchFactor(self.indic, v)
        self.layout().setStretchFactor(self.pad, v_max - v)

    def set_color(self, color: QColor):
        self.indic.set_color(color)


class SignalTitleBar(QWidget):
    def __init__(self, text: str, color: QColor, parent: 'HDBar'):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(QLabel(text, self))
        self.layout().addStretch(0)
        self.set_color(color)

    def set_color(self, color: QColor):
        self.setStyleSheet("background-color: %s" % color2style(color))


class HDBar(QWidget):
    """One signal's row."""
    __ss: AnalogSignalSuit
    title: SignalTitleBar
    harm: list[SignalHarmBar]

    def __init__(self, ss: AnalogSignalSuit, parent: 'HDTable'):
        super().__init__(parent)
        self.__ss = ss
        self.title = SignalTitleBar(ss.signal.sid, ss.color, self)
        self.harm = list()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.title)
        for i in (1, 2, 3, 5):
            hrm = SignalHarmBar(i, self)
            self.harm.append(hrm)
            self.layout().addWidget(hrm)
        self.__slot_set_color()
        self.__slot_ptr_moved(self.parent().hdwin.t_i)
        parent.hdwin.signal_ptr_moved.connect(self.__slot_ptr_moved)
        ss.signal_chg_color.connect(self.__slot_set_color)

    def __slot_ptr_moved(self, t_i: int):
        # FIXME: chk h1 = 0
        # t_i = self.parent().hdwin.t_i  # current pint
        # - get all values
        v = [abs(self.__ss.hrm(h.h_no, t_i)) for h in self.harm]
        # - calc max
        v_max = round(100 * max(v)/v[0])
        # - paint them
        self.harm[0].set_value(100, v_max)
        self.harm[1].set_value(round(100 * v[1]/v[0]), v_max)
        self.harm[2].set_value(round(100 * v[2]/v[0]), v_max)
        self.harm[3].set_value(round(100 * v[3]/v[0]), v_max)

    def __slot_set_color(self):
        c = self.__ss.color
        self.title.set_color(c)
        for h in self.harm:
            h.set_color(c)

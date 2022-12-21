"""Find signal"""
from typing import Optional

from PyQt5.QtWidgets import QInputDialog

from iosc.sig.widget.common import SignalSuit


class FindDialog(QInputDialog):
    __ss_found: Optional[SignalSuit]

    def __init__(self, parent: 'SignalBarTable'):
        super().__init__(parent)
        self.__ss_found = None
        self.setWindowTitle("Search signal")
        self.setInputMode(self.InputMode.TextInput)
        self.setLabelText("Search signal")
        self.textValueChanged.connect(self.__slot_on_the_fly)
        self.finished.connect(self.__slot_post_close)

    def __deselect_old(self):
        if self.__ss_found:
            self.__ss_found.set_highlight(False)
            self.__ss_found = None

    def __slot_on_the_fly(self, text: str):
        if text:
            if ss := self.parent().find_signal_worker(text):  # found
                # TODO: not red bg
                if ss != self.__ss_found:
                    self.__deselect_old()
                    self.__ss_found = ss
                    self.__ss_found.set_highlight(True)
            else:  # not found
                self.__deselect_old()
                # TODO: red bg
        else:  # clear selection
            self.__deselect_old()

    def __slot_post_close(self, _: int):
        self.__deselect_old()

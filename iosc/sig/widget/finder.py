"""Find signal."""
from typing import Optional

from PyQt5.QtWidgets import QInputDialog

from iosc.sig.widget.sigsuit import SignalSuit


class FindDialog(QInputDialog):
    """'Find signal' dialog."""

    __ss_found: Optional[SignalSuit]

    def __init__(self, parent: 'SignalBarTable'):  # noqa: F821
        """Init FindDialog object."""
        super().__init__(parent)
        self.__ss_found = None
        self.setOption(self.InputDialogOption.NoButtons)
        self.setWindowTitle(self.tr("Search signal"))
        self.setInputMode(self.InputMode.TextInput)
        self.setLabelText(self.tr("Search signal"))
        self.textValueChanged.connect(self.__slot_on_the_fly)
        self.finished.connect(self.__slot_post_close)

    def __deselect_old(self):
        if self.__ss_found:
            self.__ss_found.set_highlight(False)
            self.__ss_found = None

    def __highlight_found(self, found: bool):
        self.setStyleSheet('' if found else 'QInputDialog {background-color: red;}')

    def __slot_on_the_fly(self, text: str):
        if text:
            if ss := self.parent().find_signal_worker(text):  # found
                # TODO: not red bg
                self.__highlight_found(True)
                if ss != self.__ss_found:
                    self.__deselect_old()
                    self.__ss_found = ss
                    self.__ss_found.set_highlight(True)
            else:  # not found
                self.__deselect_old()
                self.__highlight_found(False)
                # TODO: red bg
        else:  # clear selection
            self.__deselect_old()
            self.__highlight_found(True)

    def __slot_post_close(self, _: int):
        self.__deselect_old()

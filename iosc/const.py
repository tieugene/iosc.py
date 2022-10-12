from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPen

COL0_WIDTH = 150  # width of Columnt 0 (SigCtrlView)
XSCALE_HEIGHT = 24  # height of timeline widget, px
XSCALE_H_PAD = 4
SIG_HEIGHT_MIN = 48  # FIXME: dirty hack
SIG_HEIGHT_DEFAULT_A = 100  # height of analog signal row, px
SIG_HEIGHT_DEFAULT_D = SIG_HEIGHT_MIN   # heigth of digital signal row, px
SIG_A_YPAD = 0.1  # top/bottom Y-pads for analog signal, part of (0.1 == 10%)
SIG_D_YMAX = 1.6   # top margin of digital signal chart, natural units
SIG_D_YMIN = -0.1   # bottom margin of digital signal chart, natural units
SIG_ZOOM_BTN_WIDTH = 32
# (moved)
X_FONT = QFont('mono', 8)  # font of timeline ticks labels
X_LABEL_COLOR = Qt.white
X_LABEL_BRUSH = QBrush(Qt.red)
Z_LABEL_COLOR = Qt.black
Z_LABEL_BRUSH = QBrush(Qt.white)
D_BRUSH = QBrush(Qt.DiagCrossPattern)
ZERO_PEN = QPen(Qt.black)
NO_PEN = QPen(QColor(255, 255, 255, 0))
MAIN_PTR_PEN = QPen(QBrush(QColor('orange')), 1)
OLD_PTR_PEN = QPen(QBrush(Qt.green), 1, Qt.DotLine)
OMP_PTR_PEN = QPen(QBrush(Qt.red), 1)
PTR_RECT_HEIGHT = 20
TICK_COUNT = 20
Y_PAD = 0.1  # upper and lower Y-padding; 0.1 == 10%
X_SCATTER_MARK = 20  # lowest px/sample to show samples as '+'
X_SCATTER_NUM = 50  # lowest px/sample to show samples as No
X_SCATTER_MAX = 100  # highest px/sample, don't expand further
X_CENTERED = True  # center view on x-scaling (glitches on True)

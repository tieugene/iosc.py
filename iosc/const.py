from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPen

COL0_WIDTH_INIT = 150  # width of Columnt 0 (SigCtrlView)
COL0_WIDTH_MIN = 50
XSCALE_HEIGHT = 24  # height of timeline widget, px
XSCALE_H_PAD = 4
SIG_HEIGHT_MIN = 50  # FIXME: dirty hack
SIG_HEIGHT_DEFAULT_A = 100  # height of analog signal row, px
SIG_HEIGHT_DEFAULT_D = SIG_HEIGHT_MIN   # heigth of digital signal row, px
SIG_A_YPAD = 0.1  # top/bottom Y-pads for analog signal, part of (0.1 == 10%)
SIG_D_YMAX = 1.6   # top margin of digital signal chart, natural units
SIG_D_YMIN = -0.1   # bottom margin of digital signal chart, natural units
SIG_ZOOM_BTN_WIDTH = 32
# (moved)
FONT_TOPBAR = QFont('mono', 8)  # font of timeline ticks labels
FONT_DND = FONT_TOPBAR
CURSOR_PTR = Qt.SplitHCursor
COLOR_LABEL_Z = Qt.black
BRUSH_LABEL_Z = QBrush(Qt.white)
COLOR_LABEL_X = Qt.white  # top xPtr label font color
BRUSH_PTR_MAIN = QBrush(Qt.red)  # top MainPtr label bg color
BRUSH_PTR_TMP = QBrush(Qt.blue)  # top MainPtr label bg color
BRUSH_D = QBrush(Qt.DiagCrossPattern)
PEN_NONE = QPen(QColor(255, 255, 255, 0))
PEN_ZERO = QPen(Qt.black)
PEN_DND = PEN_ZERO
PEN_PTR_OLD = QPen(QBrush(Qt.black), 1, Qt.DashLine)  # Main/TmpPtr old position line pen
PEN_PTR_OMP = QPen(QBrush(Qt.magenta), 1)  # OMP SCPtr pen
PEN_PTR_MAIN = QPen(BRUSH_PTR_MAIN, 1)  # MainPtr pen
PEN_PTR_TMP = QPen(BRUSH_PTR_TMP, 1, Qt.DashLine)  # TmpPtr pen
PENSTYLE_PTR_MSR = Qt.DashLine  # MsrPtr pen style
PENSTYLE_PTR_LVL = Qt.DashLine  # LVlPtr pen style
RECT_PTR_HEIGHT = 20
TICK_COUNT = 20
Y_PAD = 0.1  # upper and lower Y-padding; 0.1 == 10%
X_SCATTER_MARK = 20  # lowest px/sample to show samples as '+'
X_SCATTER_NUM = 50  # lowest px/sample to show samples as No
X_CENTERED = True  # center view on x-scaling (glitches on True)
# new 221108
LINE_CELL_SIZE = 3
Y_ZOOM_MAX = 100  # Max Y-zoom factor
Y_SCROLL_HEIGHT = Y_ZOOM_MAX * 100  # Constant YScroller width, units
X_PX_WIDTH_uS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)  # Px widhts, μs
# orange (255, 127, 39), green (0, 128, 0), red (198, 0, 0)
COLOR_SIG_DEFAULT = {'a': 16744231, 'b': 32768, 'c': 12976128}
COLOR_SIG_UNKNOWN = 0

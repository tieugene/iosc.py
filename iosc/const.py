"""Constants (global)."""
# 2. 3rd
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPen
# 3. x. const
OFG_VER = '1.0'
COL0_WIDTH_INIT = 150  # width of Columnt 0 (SigCtrlView)
COL0_WIDTH_MIN = 50
XSCALE_HEIGHT = 24  # height of timeline widget, px
XSCALE_H_PAD = 4
BAR_HEIGHT_MIN = 50  # FIXME: dirty hack
BAR_HEIGHT_D = BAR_HEIGHT_MIN   # heigth of digital signal row, px
BAR_HEIGHT_A_DEFAULT = 100  # height of analog signal row, px
SIG_A_YPAD = 0.1  # top/bottom Y-pads for analog signal, part of (0.1 == 10%)
SIG_D_YMAX = 1.6   # top margin of digital signal chart, natural units
SIG_D_YMIN = -0.1   # bottom margin of digital signal chart, natural units
SIG_ZOOM_BTN_WIDTH = 32
# (moved)
FONT_TOPBAR = QFont('mono', 8)  # font of timeline ticks labels
FONT_DND = FONT_TOPBAR
CURSOR_PTR_V = Qt.SplitHCursor
CURSOR_PTR_H = Qt.SplitVCursor
COLOR_LABEL_Z = Qt.GlobalColor.black
COLOR_LABEL_X = Qt.GlobalColor.white  # top xPtr label font color
COLOR_PTR_OLD = Qt.GlobalColor.black
COLOR_PTR_MAIN = Qt.GlobalColor.red
COLOR_PTR_TMP = Qt.GlobalColor.blue
COLOR_PTR_OMP = Qt.GlobalColor.magenta
COLOR_TIP = QColor(255, 170, 0)
COLOR_RECT = QColor(255, 170, 0, 128)  # pen color of ptr rectangle
BRUSH_LABEL_Z = QBrush(Qt.GlobalColor.white)
BRUSH_PTR_MAIN = QBrush(COLOR_PTR_MAIN)  # top MainPtr label bg color
BRUSH_PTR_TMP = QBrush(COLOR_PTR_TMP)  # top MainPtr label bg color
BRUSH_PTR_OMP = QBrush(COLOR_PTR_OMP)
BRUSH_TIP = QBrush(COLOR_TIP)
BRUSH_D = QBrush(Qt.DiagCrossPattern)
PENSTYLE_PTR_TMP = Qt.PenStyle.DashLine
PENSTYLE_PTR_MSR = Qt.PenStyle.DashLine  # MsrPtr pen style
PENSTYLE_PTR_LVL = Qt.PenStyle.DashLine  # LVlPtr pen style
PEN_NONE = QPen(QColor(255, 255, 255, 0))
PEN_ZERO = QPen(Qt.GlobalColor.black)
PEN_DND = PEN_ZERO
PEN_PTR_OLD = QPen(QBrush(COLOR_PTR_OLD), 1, PENSTYLE_PTR_TMP)  # Main/TmpPtr old position line pen
PEN_PTR_MAIN = QPen(BRUSH_PTR_MAIN, 1)  # MainPtr pen
PEN_PTR_TMP = QPen(BRUSH_PTR_TMP, 1, Qt.PenStyle.DashLine)  # TmpPtr pen
PEN_PTR_OMP = QPen(QBrush(COLOR_PTR_OMP), 1)  # OMP SCPtr pen
RECT_PTR_HEIGHT = 20
TICK_COUNT = 20
Y_PAD = 0.1  # upper and lower Y-padding; 0.1 == 10%
X_SCATTER_MARK = 10  # lowest px/sample to show samples as '+'
X_SCATTER_NUM = 50  # lowest px/sample to show samples as No
X_CENTERED = True  # center view on x-scaling (glitches on True)
# new 221108
LINE_CELL_SIZE = 1
Y_ZOOM_MAX = 100  # Max Y-zoom factor
Y_SCROLL_HEIGHT = Y_ZOOM_MAX * 100  # Constant YScroller width, units
X_PX_WIDTH_uS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)  # Px widhts, μs
COLOR_SIG_DEFAULT = {'a': QColor.fromRgb(255, 127, 39), 'b': QColor.fromRgb(0, 128, 0), 'c': QColor.fromRgb(198, 0, 0)}
COLOR_SIG_UNKNOWN = QColor.fromRgb(0, 0, 0)
YS_SINGLE_STEP = 100  # BarPlotWidget.YScroller.singleStep(), default=1
i18N_DIR = 'i18n'
# QSS_DIR = '../contrib/qss'    #275: Styling off

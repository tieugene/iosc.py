"""gfx_ppreview/consts: constants"""
# 1. std
# 2. 3rd
from PyQt5.QtGui import QFont
# x. consts
# - user defined
DEBUG = False  # paint borders around some items
PORTRAIT = False  # initial orientation
# - hardcoded
W_PAGE = (1130, 748)  # Page width landscape/portrait; (A4-10mm)@100dpi
W_LABEL = 105  # Label column width, dots, ~11 chars
H_HEADER = 56  # Header height, dots, =4×14
H_ROW_BASE = 36  # Base (B-only) bar height in landscape mode, dots, was 28=2×14
H_ROW_GAP = 5  # V-gap from margin to signals graph, dots
H_BOTTOM = 20  # Bottom scale height, dots
H_B_MULT = 1/5  # Height multiplier for B-sigal graph against A-signal one, 0..1
FONT_MAIN = QFont('mono', 8)  # 7×14

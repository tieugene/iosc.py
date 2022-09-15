"""SVG icons"""
from enum import Enum

from PyQt5.QtCore import QXmlStreamReader, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer

vzoom_in = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="5,6 10,1 15,6" stroke-width="1" stroke="black" fill="none"/>
    <polyline points="5,14 10,19 15,14" stroke-width="1" stroke="black" fill="none"/>
</svg>'''
vzoom_out = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="5,1 10,6 15,1" stroke-width="1" stroke="black" fill="none"/>
    <polyline points="5,19 10,14 15,19" stroke-width="1" stroke="black" fill="none"/>
</svg>'''
hzoom_in = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="6,5 1,10 6,15" stroke-width="1" stroke="black" fill="none"/>
    <polyline points="14,5 19,10 14,15" stroke-width="1" stroke="black" fill="none"/>
</svg>'''
hzoom_out = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="1,5 6,10 1,15" stroke-width="1" stroke="black" fill="none"/>
    <polyline points="19,5 14,10 19,15" stroke-width="1" stroke="black" fill="none"/>
</svg>'''
shifted_orig = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <path d="M1,10 Q5,0 10,10 T19,10" stroke-width="1" stroke="black" fill="none"/>
    <line x1="1" y1="19" x2="19" y2="19" stroke-width="1" stroke="black"/>
</svg>'''
shifted_center = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <path d="M1,10 Q5,0 10,10 T19,10" stroke-width="1" stroke="black" fill="none"/>
    <line x1="1" y1="10" x2="19" y2="10" stroke-width="1" stroke="black"/>
</svg>'''
pors_p = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="5,19 5,1 15,1 15,19" stroke-width="1" stroke="black" fill="none"/>
</svg>'''
pors_s = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <path stroke-width="1" stroke="black" fill="none"
        d="M5,1 L9,1 Q18,6 9,10 Q14,10 15,14 T10,19 L5,19 Z"/>
</svg>'''


class ESvgSrc(Enum):
    VZoomIn = vzoom_in
    VZoomOut = vzoom_out
    HZoomIn = hzoom_in
    HZoomOut = hzoom_out
    ShiftOrig = shifted_orig
    ShiftCentered = shifted_center
    PorsP = pors_p
    PorsS = pors_s


def svg_icon(src: ESvgSrc) -> QIcon:
    svg_renderer = QSvgRenderer(QXmlStreamReader(src.value))
    pix = QPixmap(svg_renderer.defaultSize())
    pix.fill(Qt.transparent)
    svg_renderer.render(QPainter(pix))
    return QIcon(pix)

"""SVG icons"""
from enum import Enum

from PyQt5.QtCore import QXmlStreamReader, Qt
from PyQt5.QtGui import QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer

vzoom_in = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="5,6 10,1 15,6" stroke-width="1" stroke="currentColor" fill="none"/>
    <polyline points="5,14 10,19 15,14" stroke-width="1" stroke="currentColor" fill="none"/>
</svg>'''
vzoom_out = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="5,1 10,6 15,1" stroke-width="1" stroke="currentColor" fill="none"/>
    <polyline points="5,19 10,14 15,19" stroke-width="1" stroke="currentColor" fill="none"/>
</svg>'''
hzoom_in = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="6,5 1,10 6,15" stroke-width="1" stroke="currentColor" fill="none"/>
    <polyline points="14,5 19,10 14,15" stroke-width="1" stroke="currentColor" fill="none"/>
</svg>'''
hzoom_out = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <polyline points="1,5 6,10 1,15" stroke-width="1" stroke="currentColor" fill="none"/>
    <polyline points="19,5 14,10 19,15" stroke-width="1" stroke="currentColor" fill="none"/>
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
pdf = '''<?xml version="1.0" encoding="utf-8"?>
<svg width="1792" height="1792" viewBox="0 0 1792 1792" xmlns="http://www.w3.org/2000/svg">
    <path d="M1596 380q28 28 48 76t20 88v1152q0 40-28 68t-68 28h-1344q-40 0-68-28t-28-68v-1600q0-40 28-68t68-28h896q40 0 88 20t76 48zm-444-244v376h376q-10-29-22-41l-313-313q-12-12-41-22zm384 1528v-1024h-416q-40 0-68-28t-28-68v-416h-768v1536h1280zm-514-593q33 26 84 56 59-7 117-7 147 0 177 49 16 22 2 52 0 1-1 2l-2 2v1q-6 38-71 38-48 0-115-20t-130-53q-221 24-392 83-153 262-242 262-15 0-28-7l-24-12q-1-1-6-5-10-10-6-36 9-40 56-91.5t132-96.5q14-9 23 6 2 2 2 4 52-85 107-197 68-136 104-262-24-82-30.5-159.5t6.5-127.5q11-40 42-40h22q23 0 35 15 18 21 9 68-2 6-4 8 1 3 1 8v30q-2 123-14 192 55 164 146 238zm-576 411q52-24 137-158-51 40-87.5 84t-49.5 74zm398-920q-15 42-2 132 1-7 7-44 0-3 7-43 1-4 4-8-1-1-1-2-1-2-1-3-1-22-13-36 0 1-1 2v2zm-124 661q135-54 284-81-2-1-13-9.5t-16-13.5q-76-67-127-176-27 86-83 197-30 56-45 83zm646-16q-24-24-140-24 76 28 124 28 14 0 18-1 0-1-2-3z"/>
</svg>'''  # https://github.com/Rush/Font-Awesome-SVG-PNG/blob/master/black/svg/file-pdf-o.svg


class ESvgSrc(Enum):
    VZoomIn = vzoom_in
    VZoomOut = vzoom_out
    HZoomIn = hzoom_in
    HZoomOut = hzoom_out
    ShiftOrig = shifted_orig
    ShiftCentered = shifted_center
    PorsP = pors_p
    PorsS = pors_s
    PDF = pdf


def svg_icon(src: ESvgSrc) -> QIcon:
    svg_renderer = QSvgRenderer(QXmlStreamReader(src.value))
    pix = QPixmap(svg_renderer.defaultSize())
    pix.fill(Qt.transparent)
    svg_renderer.render(QPainter(pix))
    return QIcon(pix)

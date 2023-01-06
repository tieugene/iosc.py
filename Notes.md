# Notes

## Math (20230105):

- 'Math' to separate section
- From simple to complex
- Group then by conversion(?)/Arithm/Simmetric
- For each group:
  + Common part
  + Differences (each)
- For all - Comparing to ordinar A-sig::
  + Similarity (e.g. pointers)
  + Difference
- CRUD:
  + 'C' - described (in progress)
  + 'R' - partialy; e.g.:
    - Switchers reaction:
      + As&hellip; (nothing to do?)
      + PorS (=> switch source)
      + Orig/Centered (?)
    - Tools
  + 'U' - none
  + 'D' - none
- Del pictures:
  + not add something
  + but conflicts with text
  + TR is _what_ to do but pictures describe _how_ to do
- 'Use as ordinary' need separate section
- WTF [non-]harmonic signal?

## Signal table:

- [x] **QTableWidget + Line in cell**
- [ ] QGridLayout + Line
- [ ] QGraphicalGridLayout + Line
- [ ] QRubberBand (band)
- [ ] QSizeGrip (grip == catch (band))
- [x] RTFM QHeaderView (resize by margin: mouseXEvent())
- [x] QSplitters: parent widget not v-resizable
- [x] QListWidget + Line as cell: rows not v-resizable
- [x] QTableWidget + Line ac cell: too complex

### Variants:

- [x] QTableWidget:
  + &ominus; not resizable by cells
  + &ominus; cell independent
- [ ] QTableWidget + Lines as cells
  + &oplus; Drop over only
  + &ominus; Too complex calc/navigation
- [ ] QTableWidget + Lines in cells
- [x] QListWidget:
  + not resizable rows
  + not resizable col (?)
- [ ] QAbstractItemView + (QAbstractItemDelegate | model):
  + ...
- [ ] QGridLayout + Lines
- [x] QSplitter x 2:
  + &ominus; not v-resize parent widget
  + &ominus; DnD
  + &ominus; not scrollable
- QGraphics*:
  + QGraphicsLayout:
    * QGraphicsGridLayout
    * QGraphicsAnchorLayout (`examples/graphicsviews/anchorlayout.py`)
  
Line = QFrame().setFrameShape(QtWidgets.QFrame.VLine)

## RTFM

- [PyQt5 Tutorial](https://www.pythonguis.com/pyqt5-tutorial/)
- [Another tutorial](https://www.bogotobogo.com/Qt/)
- [Qt](https://evileg.com/ru/knowledge/qt/):

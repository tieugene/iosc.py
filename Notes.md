# Notes

## Signal table:

- [x] **QTableWidget + Line as cell**
- [ ] QGridLayout + Line
- [ ] QGraphicalGridLayout + Line
- [ ] QRubberBand (band)
- [ ] QSizeGrip (grip == catch (band)
- [ ] RTFM QHeaderView (resize by margin: mouseXEvent())
- [x] QSplitters: parent widget not v-resizable
- [x] QListWidget + Line as cell: rows not v-resizable

### Variants:

- [x] QTableWidget:
  + &ominus; not resizable by cells
  + &ominus; cell independent
- [ ] QTableWidget + Lines as cells
  + &oplus; Drop over only
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

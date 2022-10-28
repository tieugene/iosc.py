# TODO

Current job: [row/sig join/move/unjoin](https://github.com/tieugene/iosc.py/milestone/11)

- [ ] 0.3.0 demo
- [ ] ~~#166: Hide/Show~~
  + Requires centralized signal control
- [ ] ~~#167 Digit scatters~~
  + Requires C++ sample => ?
- [ ] ~~#174: Row shift~~
  + Table: fix vscroller + decrease table [column] width
  + List: ?

## Hot:
- RTFM QHeaderView (resize by margin)
- QTableWidget + Line as cell
- QListWidget + Line as cell
- QGridLayout + Line
- QGraphicalGridLayout + Line

## 0.3.0:

- SignalListTable(QListWidget)
  + ::setItemWidget()
-  #59 (0.p.x)
- #123 (0.u.x)
- #130 (0.p.x)
- #133 (0.p.x)
- #146 (0.u.i)
- #166 (0.2.0)
- #174 (0.2.0)
- *centralized row/sig storage*
- sig_table: deselect on mouse_up

What 2 do:
- Memory
- UI:
  + h-splitter
  + v-splitter
- PX:
  + Logic (e.g. hide/show)

### Variants:

- QTableWidget:
  + &ominus; not resizable by cells
  + &ominus; cell independent
- QTableWidget + Lines in cells
- QTableWidget + Lines as cells
- QListWidget:
  + not resizable rows
  + not resizable col (?)
- QAbstractItemView + (QAbstractItemDelegate | model):
  + ...
- QGridLayout + Lines
- QSplitter x 2:
  + &ominus; DnD
  + &ominus; not scrollable
- QGraphics*:
  + QGraphicsLayout:
    * QGraphicsGridLayout
    * QGraphicsAnchorLayout (`examples/graphicsviews/anchorlayout.py`)
  
Line = QFrame().setFrameShape(QtWidgets.QFrame.VLine)

# Summary

- px 8/11 not critical
- ui 7/ 7 not critical
- ux 6/ 7 Rq
- 02 ?/ 3
---
Summary: …/28

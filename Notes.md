# Notes

- IDEA: store signal xPtrs in Signal
- X-scale glitch:
  + &check; Start
  + &check; X-zoom in
  + &check; X-resize to max
  + &times; X-zoom out

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

## YSlider

Variants:

- *chg pagestep (range = base * zoom_y_max)*
- ~~chg range (page = base)~~

## X-scaling:

- Main value: precision (px/s):
  + min: ... (1px = 1ms, grid = 100ms, 1s == 1 Kpx)
  + max: ... (1px = 1&mu;s, grid = 0.1ms, 1s = 1 Mpx)
- Steps (10):
  + prec (px/s): 1/2/5 * 10&#8319; (n = 3..6) = 1K..1M
  + px weight (&mu;s/px): 1..1000

### 2do:

Dst:
- XScroller
- TopBar
- BarPlot

Src:
- [x] Signal windows resize (TopBar):
  + [x] XScroller:
    * [x] setPageSize(TopBar width)
    * [x] setMaximum(x_width - pageSize())
    * [x] [setValue(recalc)]
  + [x] TopBar/BarPlot: rerange_x
- [x] x-zoom:
  + [x] XScroller:
    * [x] setMaximum(x_width - pageSize())
    * [x] [setValue(recalc)]
  + [x] TopBar/BarPlot:
    * [x] rerange_x
    * [x] grid
- [x] XScroller value change:
  + [x] TopBar/BarPlot: rerange_x

## Samples:

- `IMF3R-7783--13-03-11-15-19-07.cfg`:
  + Samples: 120
  + Freq: 50 Hz
  + Rate: 600 Hz
  + SPP: 12
  + Sample width, ms: 1.(6)
  + Z-point: &numero;49

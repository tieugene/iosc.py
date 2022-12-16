# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [x] Get i-slice
- [x] Canvas:
  + [x] Header
  + [x] Grid
  + [x] Ptrs (main, OMP, tmp)
- [x] Payload (rows):
  + [x] Label
  + [x] Graph
  + [x] Ptrs (Msr, Lvl)
- [x] FIXME:
  + [x] Separate custom print options buttons
  + [x] i_range expand
  + [x] Ptrs on/off (global)
  + [x] Extra (left) grid items
  + [x] bar.is_bool labels too low (? html style ?)
  + [x] Not refreshed (exec_ \[>slot_paint_request\])
  + [x] Ptrs on/off (local)
  + [x] Modal prn dialog

## Samples:
- QPrint:
  - `itemviews/spreadseet/spreadsheet.py` (preview; QTableView().render(printer)
  - ~~`orderform.py`~~ (print only, to pdf; QTextEdit().print_()
  - ~~`textedit.py`~~ (preview; QTextEdit().print_())
- [Print to PDF](https://wiki.qt.io/Exporting_a_document_to_PDF)
- QPdfWriter:
- [QGraphicsScene &rArr; QPrinter](https://www.qtcentre.org/threads/47972-Render-QGraphicsScene-to-a-QPrinter-to-export-PDF)
- [FAQ 2](https://stackoverflow.com/questions/35034953/printing-qgraphicsscene-cuts-objects-in-half)

## RTFM:
- QSplineSeries
- [spline](https://www.toptal.com/c-plus-plus/rounded-corners-bezier-curves-qpainter)
- **QGraphicsGridLayout**
- [disable transform](https://stackoverflow.com/questions/1222914/qgraphicsview-and-qgraphicsitem-don%C2%B4t-scale-item-when-scaling-the-view-rect)
- [Scene border](https://www.qtcentre.org/threads/13814-how-to-enable-borders-in-QGraphicsScene)
- [Tic align](https://www.qtcentre.org/threads/51168-QGraphicsTextItem-center-based-coordinates)

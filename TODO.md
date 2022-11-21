# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [x] Header
- [ ] Table:
  + [x] Border
  + [x] Bottom line (upper digits)
  + [ ] Grid (lines + digits)
- [ ] Rows:
  + [ ] Label
  + [ ] Plot:
    * [ ] zero
    * [ ] graph(pos: point, size: rect(width(x0..x1), height(px)))
  + [ ] Underline

Note: 1 dot = 0.254mm (0.01"); A4 - 10mm = 190x277mm = 748x1130 dots
- 1130 = 54+20+6x176
- 748 = 56+20+6x112

## Plot.graph:

Src data:
- common (on exec_():
  + \[X0..X1]:float (s)
- each signal:
  + Y [round_down(X0)..round_up(X1)]:float
  + Y range (min/max):float

dst_size = f(orientation) = fixed

Dst: ([X0..X1, ]sig(=>Y*), dst_size:rect) -> QGfxObject:
- plot y=0
- plot polyline y0..y1
- clip to x0..x1

## Samples:
- QPrint:
  - `itemviews/spreadseet/spreadsheet.py` (preview; QTableView().render(printer)
  - ~~`orderform.py`~~ (print only, to pdf; QTextEdit().print_()
  - ~~`textedit.py`~~ (preview; QTextEdit().print_())
- [Print to PDF](https://wiki.qt.io/Exporting_a_document_to_PDF)
- QPdfWriter: &hellip;
- [FAQ](https://www.qtcentre.org/threads/47972-Render-QGraphicsScene-to-a-QPrinter-to-export-PDF)
- [FAQ 2](https://stackoverflow.com/questions/35034953/printing-qgraphicsscene-cuts-objects-in-half)

## Find:
- [x] Custom QPrintPreviewDialog(): QPrintPreviewDialog().findChildren()
- [x] Split QLayout|QGRaphicsScene by pages: QPrinter().pageRect()
- [ ] QPdfWriter(QPaint) sample
- [ ] QGraphicsView.render() + page break (printer.newPage())

## Classes:
- QPainter:
  + QPaintDevice
    * QPagedPaintDevice
      - QPdfWriter
      - QPrinter

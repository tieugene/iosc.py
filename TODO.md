# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [ ] Header
- [ ] Table:
  + [ ] Signal name column\[, value]
  + [ ] Plot column:
    * [ ] Signal graph
    * [ ] Grid
    * [ ] Main ptr
- [ ] Bottom time scale (digits only)

## Samples:
- QPrint:
  - `itemviews/spreadseet/spreadsheet.py` (preview; QTableView().render(printer)
  - ~~`orderform.py`~~ (print only, to pdf; QTextEdit().print_()
  - ~~`textedit.py`~~ (preview; QTextEdit().print_())
- [Print to PDF](https://wiki.qt.io/Exporting_a_document_to_PDF)
- QPdfWriter: &hellip;

## Find:
- [x] Custom QPrintPreviewDialog(): QPrintPreviewDialog().findChildren()
- [x] Split QLayout|QGRaphicsScene by pages: QPrinter().pageRect()
- [ ] QPdfWriter(QPaint) sample

## Classes:
- QPainter:
  + QPaintDevice
    * QPagedPaintDevice
      - QPdfWriter
      - QPrinter

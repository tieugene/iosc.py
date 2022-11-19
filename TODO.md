# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

RTFM: [sample](https://wiki.qt.io/Exporting_a_document_to_PDF)

- [ ] Inject 5 x Chqckboxes:
  - [ ] Color/BW
  - [ ] Signal names
  - [ ] Scale coefficient?
  - [ ] Pinters
  - [ ] Signal values on main pointer

## Samples:
- `itemviews/spreadseet/spreadsheet.py` (preview; QTableView().render(printer)
- ~~`orderform.py`~~ (print only, to pdf; QTextEdit().print_()
- ~~`textedit.py`~~ (preview; QTextEdit().print_())

## Find:
- Custom QPrintPreviewDialog():
  + QPrintPreviewDialog().findChildren()
- Split QLayout|QGRaphicsScene by pages:
  + QPrinter().pageRect()

## Plan:
- [ ] Header
- [ ] Table:
  + [ ] Signal name column\[, value]
  + [ ] Plot column:
    * [ ] Signal graph
    * [ ] Grid
    * [ ] Main ptr
- [ ] Bottom time scale (digits only)

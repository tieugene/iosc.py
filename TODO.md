# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [ ] Try scene w/o view
- [ ] Paging:
  + 1 view, 1 scene, multi header/footer, shift (too complex)
  + 1 view, N scenes
- [ ] Analog/Binary switch

## Layout:

- [x] Header
- [ ] Table:
  + [x] Border
  + [x] Bottom line (upper digits)
  + [ ] Grid (lines + digits)
- [ ] Rows:
  + [x] Label
  + [ ] Plot:
    * [ ] zero
    * [ ] graph(pos: point, size: rect(width(x0..x1), height(px)))
  + [x] Underline

Note: 1 dot = 0.254mm (0.01"); A4 - 10mm = 190x277mm = 748x1130 dots
- 1130 = 42+12+6x176+20 (head+gap+signals+footer)
- 748 = 42+14+6x112+20

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
- [QGraphicsScene &rArr; QPrinter](https://www.qtcentre.org/threads/47972-Render-QGraphicsScene-to-a-QPrinter-to-export-PDF)
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

## Analog:

Печатает:

- _Весь_ сигнал (в ширину; отсюда и "печатать имена сигналов на каждой странице)
- Печатает совмещенные, как на экране
- По высоте количество как на экране как если на весь экран
- Масштаб неизвестен:
  + Альбом - по горизонтали - как если на весь экран, по вертикали - пропорционально
  + Портрет - хез (типа по вертикали так же, по горизонтали обрезает справа)

Мы себе:
- Горизонтально: сколько на экране, столько и на бумаге (!)
- Вертикально - порпорционально, как на экране
- Печатать bars
- весь сигнал от начала до конца.
- &rdsh; wide scene + shift + рамочка сверху

Но это не точно.

# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [x] Get i-slice  
- [x] Canvas:
  + [x] Header
  + [x] Grid
  + [x] Ptrs (main, OMP, tmp)
- [ ] Payload (rows):
  + [x] Label
  + [x] Graph
  + [ ] Ptrs (Msr, Lvl)
- [ ] FIXME:
  + [x] Separate custom print options buttons
  + [x] i_range expand
  + [x] Ptrs on/off (global)
  + [?] Extra (left) grid items
  + [ ] bar.is_bool labels too low (? html style ?)
  + [ ] Not refreshed (Header.pors, grid step)
  + [ ] 2x __init__
  + [ ] Signal sanity check

Note:
- 1 dot = 0.254mm (0.01")
- A4 - 210×297mm = 827×1170 dots
- A4 - 10mm = 190×277mm = 748×1130 dots:
  + 1130 = 42+12+(6×176/24×44)+20 (head+gap+signals+footer)
  + 748 = 42+14+(6×112/24×28)+20

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
- QPdfWriter:
- [QGraphicsScene &rArr; QPrinter](https://www.qtcentre.org/threads/47972-Render-QGraphicsScene-to-a-QPrinter-to-export-PDF)
- [FAQ 2](https://stackoverflow.com/questions/35034953/printing-qgraphicsscene-cuts-objects-in-half)

## Analog&trade;:

Печатает:

- _Весь_ сигнал (в ширину; отсюда и "печатать имена сигналов на каждой странице)
- Печатает совмещенные, как на экране
- По высоте количество как на экране как если на весь экран
- Масштаб неизвестен:
  + Альбом - по горизонтали - как если на весь экран, по вертикали - пропорционально
  + Портрет - хез (типа по вертикали так же, по горизонтали обрезает справа)

Мы себе:
- Горизонтально: сколько на экране, столько и на бумаге (!)
- Вертикально - пропорционально, как на экране
- Печатать bars
- весь сигнал от начала до конца (?)
- &rdsh; wide scene + shift + рамочка сверху

Но это не точно.

## RTFM:
- QSplineSeries
- [spline](https://www.toptal.com/c-plus-plus/rounded-corners-bezier-curves-qpainter)
- **QGraphicsGridLayout**
- [disable transform](https://stackoverflow.com/questions/1222914/qgraphicsview-and-qgraphicsitem-don%C2%B4t-scale-item-when-scaling-the-view-rect)
- [Scene border](https://www.qtcentre.org/threads/13814-how-to-enable-borders-in-QGraphicsScene)
- [Tic align](https://www.qtcentre.org/threads/51168-QGraphicsTextItem-center-based-coordinates)

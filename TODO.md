# TODO

Current job: [0.3.2. PDF](https://github.com/tieugene/iosc.py/issues/191)

- [x] Get i-slice  
- [ ] Canvas:
  + [x] Header
  + [x] Grid
  + [ ] Ptrs (main, OMP, tmp)
- [ ] Payload (rows):
  + [x] Label
  + [x] Graph
  + [ ] Ptrs (Msr, Lvl)
- [ ] FIXME:
  + [ ] Extra (left) grid items
  + [ ] Header.pors not switching
  + [ ] bar.is_bool labels too low (? html style ?)

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
- Вертикально - пропорционально, как на экране
- Печатать bars
- весь сигнал от начала до конца (?)
- &rdsh; wide scene + shift + рамочка сверху

Но это не точно.

## 20221122:
- Берем с экрана ширины надписи в кол0 (это будет ширина кол0) и кол1. Это будет ширина в dots.
- Берем из printer ширину и высоту pagesize. Это будут пропорции.  
- Набиваем bar'ами высоту до пропорции
- Bar рендерим как есть (toPainter()) (?)

## Q&A:
- Интервал: a) "как на экране" (ТЗ); ~~"все" (Аналог)~~
- ~~С высотой непонятно вообще~~ сказано 6/24, значит 6/24

## 20221124:
- Рисуют SignalBar и SignalSuit
- H-size: fixed (portrait/landscape)
- W-size:
  + labels: fixed (100)
  + plot: fixed (1000)
- then transform:
  + header: h: skip, w: cut
  + rows: resize:
    + labels: cut
    + plot: resize
  + footer: h: skip, w: resize
&deg;

## RTFM:
- QSplineSeries
- [spline](https://www.toptal.com/c-plus-plus/rounded-corners-bezier-curves-qpainter)
- **QGraphicsGridLayout**
- [disable transform](https://stackoverflow.com/questions/1222914/qgraphicsview-and-qgraphicsitem-don%C2%B4t-scale-item-when-scaling-the-view-rect)
- [Scene border](https://www.qtcentre.org/threads/13814-how-to-enable-borders-in-QGraphicsScene)
- [Tic align](https://www.qtcentre.org/threads/51168-QGraphicsTextItem-center-based-coordinates)

## 20221214

Grid: берем t0..tmax и по модулю step

# TODO

Current job: [0.3.0](https://github.com/tieugene/iosc.py/milestone/12)

- [ ] Diagram:
  + [x] textitem (text, anchor, radius)
  + [x] &rdsh; axis label
  + [x] Arrow
  + [x] Vector = Arrow + Label
- [x] Select signals
- [ ] Table
- [ ] Update table/diagram by signal (name, color) & ptr (angle, value)
- [ ] Select Ptr

## Vector diagram

Variant (Circle):

+ Qt graphics:
  + QGraphicsItem (rtfm robot) + graphicsscene + graphicsview
  + &rdsh;QGraphicsObject == QGI+QObject (signa/slot)
  + ~~&rdsh;QGraphicsWidget~~ (too much)
  + QWidget.paintEvent() (painting/)
    + &rdsh;QPainterPath()
- ~~QCustomPlot~~:
  + QCPPolarGraph
  + QCPAbstractItems:
    * QCPItemEllipse
    * QCPItemLine

### RTFMs:

- PqyQt5/examples/:
  + widgets/windowsflags.py
  + graphicsview/diagramscene/py (gfx items)
- [QCPPolarGraph announce](https://www.qcustomplot.com/index.php/news)
- [PyQt5 Tutorial](https://www.pythonguis.com/pyqt5-tutorial/)
- [Another tutorial](https://www.bogotobogo.com/Qt/)
- Habr:
  + [good](https://habr.com/ru/post/182142/)
  + [bad1](https://habr.com/ru/post/182614/)
  + [bad2](https://habr.com/ru/post/183432/)
  + [code](https://github.com/DancingOnWater/GraphicsScenePlot)

# TODO

Current job: [0.3.1](https://github.com/tieugene/iosc.py/milestone/13)

- [x] Diagram:
  + [x] textitem (text, anchor, radius)
  + [x] &rdsh; axis label
  + [x] Arrow
  + [x] Vector = Arrow + Label
- [x] Select signals
- [x] Initial fill:
  + [x] Table (name, color, values)
  + [x] Diagram (name, color, angle)
- [x] Update by MainPtr:
  + [x] Table (values)
  + [x] Diagram (angle)
* […] Align angle to:
  + [x] North
  + [ ] Base signal
- [ ] Select Ptr
- [ ] Update by selected Ptr
- [ ] Use base signal
- [ ] Hide/Show
- [ ] Update name, color
- [ ] FIXME: SigVector arrow color

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

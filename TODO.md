# TODO

Current job: [0.3.0](https://github.com/tieugene/iosc.py/milestone/12)

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
- [Chart sample](https://github.com/DancingOnWater/GraphicsScenePlot)
- &rdsh; [Dox of it](https://habr.com/ru/post/182614/)

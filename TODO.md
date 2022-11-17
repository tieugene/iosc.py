# TODO

Current job: [0.3.1. CVD](https://github.com/tieugene/iosc.py/issues/190)

- […] TmpPtr:
  + [ ] Select
  + [ ] Update by selected TmpPtr
  + [ ] Chg TmpPtrs:
    * [ ] Add: add to list
    * [ ] Del: switch to MainPtr
    * [ ] Upd: do nothing
- [ ] Hide/Show signals
- [ ] Update name, color
- [ ] CVD on/off
- [ ] Split by modules

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
- [Notes](Notes.md)

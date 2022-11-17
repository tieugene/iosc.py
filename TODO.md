# TODO

Current job: [0.3.1. CVD](https://github.com/tieugene/iosc.py/issues/190)

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

## SWitch Ptr

Signals:

- oscwin.signal_ptr_moved_main(int):
  + cvdwin.__slot_ptr_moved_main
- oscwin.signal_ptr_moved_tmp(int):
  + cvdwin.__slot_ptr_moved_main

- oscwin.signal_ptr_add_tmp(uint:int):
  + actions_ptr: add item
- oscwin.signal_ptr_del_tmp(uint:int):
  + _actions_ptr: del item
  + _actions_ptr: switch to main_

- action_ptr.triggered():
  + cvdwin: switch ptr (=> i)
  + cvdwin.__slot_ptr_moved_main

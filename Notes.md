# Notes

## TZ (230216):

According to 2.4.1.1.:

- В качестве исходных сигналов для расчёта используются 1 гармоники исходных несмещенных аналоговых сигналов
- Расчётные сигналы могут быть источниками для новых расчётных сигналов
- Для расчётных сигналов требуется отображать только их мгновенное значение (As is) (в каком виде? Комплексное или как?)

2.4.1.2. Подпункт "Преобразования":
- Входной сигнал: комплексный (комплексное значение первой гармоники исходного сигнала, иной расчётный сигнал и т.д.).
- Что значит "и т.д."?
- отображается только мгновенные значения (As is) - в каком виде?

Итого:
- Входной сигнал расчета - только комплексный (да)
- &rArr; Расчетный сигнал - только комплексный (да)
- Выход Преобразования == расчетный сигнал (да)
- Выход Преобразования - комплексный (нет)

## Math (20230105):
- Signal behavior to separate section
- 'Math' to separate section
- Del pictures:
  + not add something
  + but conflicts with text
  + TR is _what_ to do but pictures describe _how_ to do
- From simple to complex
- Group then by conversion(?)/Arithm/Simmetric
- For each group:
  + Common part
  + Differences (each)
- For all - Comparing to ordinar A-sig:
  + Similarity (e.g. pointers)
  + Difference
- CRUD:
  + 'C' - described (in progress)
  + 'R' - partialy; e.g.:
    - Switchers reaction:
      + As&hellip; (nothing to do?)
      + PorS (=> switch source)
      + Orig/Centered (?)
    - Tools
  + 'U' - none
  + 'D' - none
- 'Math use in math' needs separate section
- WTF (non-)harmonic signal?


## Hierarchy:

- `sigsuit.SignalSuit`: GUI wrapper for&hellip;
- &rdsh;`mycomtrade.*`: non-GUI wrapper for&hellip;
- &rdsh;`comtrade.*`: raw osc data


## Signal behavior
### A(nalog)
#### Yes
- CRUD:
  + R
- Y-scale
- Switch
- Math
- Pointers (global, local)
- Tools

#### No
- CRUD:
  + C
  + U *(partialy)*
  + D

### B(oolean)
#### Yes
- Y-scale (zoom, resize) *(w/ A, complex)*:
- Pointers (global)
- Tools:
  + VT

#### No
- Y-scale (zoom, resize) *(w/o A)*:
- Switch:
  + Center
  + PorS
  + View as
+ Math
+ Pointers (local (Msr, Lvl))
+ Tools:
  + CVD
  + HD
  + OMP

### C(alculated)
#### Yes
#### No

## Signal table:
- [x] **QTableWidget + Line in cell**
- [ ] QGridLayout + Line
- [ ] QGraphicalGridLayout + Line
- [ ] QRubberBand (band)
- [ ] QSizeGrip (grip == catch (band))
- [x] RTFM QHeaderView (resize by margin: mouseXEvent())
- [x] QSplitters: parent widget not v-resizable
- [x] QListWidget + Line as cell: rows not v-resizable
- [x] QTableWidget + Line ac cell: too complex

### Variants:
- [x] QTableWidget:
  + &ominus; not resizable by cells
  + &ominus; cell independent
- [ ] QTableWidget + Lines as cells
  + &oplus; Drop over only
  + &ominus; Too complex calc/navigation
- [ ] QTableWidget + Lines in cells
- [x] QListWidget:
  + not resizable rows
  + not resizable col (?)
- [ ] QAbstractItemView + (QAbstractItemDelegate | model):
  + ...
- [ ] QGridLayout + Lines
- [x] QSplitter x 2:
  + &ominus; not v-resize parent widget
  + &ominus; DnD
  + &ominus; not scrollable
- QGraphics*:
  + QGraphicsLayout:
    * QGraphicsGridLayout
    * QGraphicsAnchorLayout (`examples/graphicsviews/anchorlayout.py`)
  
Line = QFrame().setFrameShape(QtWidgets.QFrame.VLine)

## RTFM
- [PyQt5 Tutorial](https://www.pythonguis.com/pyqt5-tutorial/)
- [Another tutorial](https://www.bogotobogo.com/Qt/)
- [Qt](https://evileg.com/ru/knowledge/qt/):

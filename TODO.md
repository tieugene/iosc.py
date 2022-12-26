# TODO

Current job: [0.3.3. Misc](https://github.com/tieugene/iosc.py/milestone/15)

- [ ] [Signal degeneration](https://github.com/tieugene/iosc.py/issues/197)
- [ ] [Signal shift](https://github.com/tieugene/iosc.py/issues/199)
- […] [X-zoom glitches](https://github.com/tieugene/iosc.py/issues/203)

## 203:

- `ComtradeWidget.signal_x_zoom.emit()`:
  + &rdsh;`TimeAxistPlot.__slot_retick()` &times;2
  + &rdsh;`BarPlot.__slot_retick()`
  + &rdsh;`SignalSuit.__slot_retick()`
  + &rdsh;`XScroller.__slot_update_range()`
    - &rdsh;?`….signal_update_plots.emit()`
- `TimeAxisPlot.resizeEvent()`: `….signal_width_changed.emit(w)`
  + &rdsh;`XScroller.__slot_update_page()`
    - &rdsh;?`….signal_update_plots.emit()`
- `XScroller.signal_update_plots.emit()`:
  + &rdsh;`TimeAxisPlot.slot_rerange()` &times;2
  + &rdsh;`BarPlot.__slot_rerange_x()`

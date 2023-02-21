# TODO

Current job: [0.3.5. Math](https://github.com/tieugene/iosc.py/milestone/17)

- [ ] #245: MyComtrade.avalues():
  + [x] `StatusSignalSuit.values()`/`AnalogSignalSuit.a_values()` | `xGraphItem.__init__()`: -1…0.(9) … -0.5…0.5 … 0.(9)…1 … Δ=0…1
  + [x] `AnalogSignalSuit._data_y()` | `.graph.setData()`: -1…0.(9) … -1…1 … 0.(9)…1 … => Δ=0…2
  + [ ] FIXME: PDF(~~y-centered~~)
  + [ ] FIXME: Screen(~~y-centered~~)
  + [ ] LvlPtr: 0…1 of y_min…y_max ∨ 0
- [ ] #250: LvlPtr: centered (limits), pors

## Adjusted

```py
# sig.widget.sigsuit.ASignalSuit._data_y()
divider = max(abs(ss.v_min), abs(ss.v_max))
# sig.pdfout.bar.AGraphItem.__init__()
divider = max(0.0, ss.v_max) - min(0.0, ss.v_min)
# common
[v / divider for v in ss.values]
```

## Calculated signals

- [ ] 2.3.4.3.1. Common (actions, menu, base things)
- [ ] 2.4.1.2. Conversions:
  + [ ] 2.4.1.2.1. Module
  + [ ] 2.4.1.2.2. Angle
  + [ ] 2.4.1.2.3. Real part
  + [ ] 2.4.1.2.4. Image part
- [ ] 2.4.1.3. Arithmetic:
  + [ ] 2.4.1.3.1. Add-cross
  + [ ] 2.4.1.3.2. Mult-cross
  + [ ] 2.4.1.3.3. Mult-const
- [ ] 2.4.1.4. Symmetric &hellip;
  - [ ] 2.4.1.4.1. F-sequence
  - [ ] 2.4.1.4.2. R-sequence
  - [ ] 2.4.1.4.3. 0-sequence

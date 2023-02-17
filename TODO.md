# TODO

Current job: [0.3.5. Math](https://github.com/tieugene/iosc.py/milestone/17)

- [ ] #245: MyComtrade.avalues()  (AnalogSignalSuit._data_y(), SignalSuit.v_slice() | xGraphItem.init())
- [ ] #248: SC/PR top labels
- [ ] #249: Harm. 0..5
- [ ] #250: LvlPtr: centered (limits), pors

## Adjusted

min|max| Δ | Si | Sa | Gi | Ga
---|---|---|----|----|----|----

### ASignalSuit._data_y():
```py
divider = max(abs(self.v_min), abs(self.v_max))
[v / divider for v in values]
```

### AGraphItem.__init__():
```py
amin = min(0.0, ss.v_min)  # adjusted absolute value
amax = max(0.0, ss.v_max)
divider = amax - amin
[v / divider for v in values]
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

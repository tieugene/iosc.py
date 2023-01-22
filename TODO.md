# TODO

Current job: [0.3.5. Math](https://github.com/tieugene/iosc.py/milestone/17)

- [ ] #111 Dynamic 'shift':
  + [x] MyComtrade.values(shift)
  + [ ] MyComtrade.value(i, shift, pors, func)
-[ ] FIXME: LvlPtr limits vs y_centered
- [ ] Add 'module' to signals

- [ ] 2.3.4.3.1. Common (actions, menu, base things)
- [ ] 2.3.4.3.2. F-sequence
- [ ] 2.3.4.3.3. R-sequence
- [ ] 2.3.4.3.4. 0-sequence
- [ ] 2.3.4.3.5. Add-cross
- [ ] 2.3.4.3.6. Mult-cross
- [ ] 2.3.4.3.7. Mult-const
- [ ] 2.3.4.3.8. Module
- [ ] 2.3.4.3.9. Angle
- [ ] 2.3.4.3.10. Real part
- [ ] 2.3.4.3.11. Image part

## Adjusted

min| max | Δ | Si | Sa | Gi | Ga |
---|---|

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

## Hierarchy:

- `sigsuit.SignalSuit`: GUI wrapper for&hellip;
- &rdsh;`mycomtrade.*`: non-GUI wrapper for&hellip;
- &rdsh;`comtrade.*`: raw osc data

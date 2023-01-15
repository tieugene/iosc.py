# TODO

Current job: [0.3.5. Math](https://github.com/tieugene/iosc.py/milestone/17)

- [ ] #111 Dynamic 'shift':
  + [x] mycomtrade.values(shift)
  + [ ] mycomtrade.value(i, shift, pors, func)
-[ ] FIXME: LvlPtr limits vs y_centered
- [ ] Add 'module' to signals

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

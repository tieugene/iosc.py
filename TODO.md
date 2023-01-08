# TODO

Current job: [0.3.5. Math](https://github.com/tieugene/iosc.py/milestone/17)

- [x] 1-button centered
- [ ] Protected `SignalSuit._signal`:
  + [x] is_bool
  + [x] sid
  + [x] uu
  + [x] info (primary, secondary, pors)
  + [x] i (cfg_save/_restore, CDVWindow/HDWindow._do_settings())
  + [ ] v_min, v_max (AGraphItem, LvlPtr)
  + [ ] get_mult (LvlPtr)
  + [ ] value[s]
- [ ] Add 'module' to signals

## Hierarchy:

- `sigsuit.SignalSuit`: GUI wrapper for&hellip;
- &rdsh;`mycomtrade.*`: non-GUI wrapper for&hellip;
- &rdsh;`comtrade.*`: raw osc data

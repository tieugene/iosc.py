# Test
## 0.3.4 => 0.3.5

##### Calls:
- [ ] AnalogSignalLabel.slot_update_value()
- [ ] &rdsh;ASignalLabel.__value_str
- [ ] &rdsh;ASignalSuit.sig2str_i(self.ss.bar.table.oscwin.main_ptr_i)
- [ ] &rdsh;ASignal.as_str_full(ASignal.value(i, cnt, pors), pors)
- [ ] &rdsh;ASignal.as_str(pors)

#### Try 3:
- LvlPtr PorS &cross;
- ValueTable lies
- CVD segfault
- HD segfault

### Deps F(c, ps, f):

- [ ] File:
  + [ ] CSV(F, ps, 0)
  + [ ] PDF(?, ?, ?)
- [ ] Ptr:
  + [ ] MainPtr(c, ps, f)
  + [ ] MsrPtr(?, ?, f=const)
  + [ ] LvlPtr(?, ?, ?)
- [ ] Tools:
  + [ ] CVD(F, ps, f=h1)
  + [ ] HD(F, *, f=h0..5)
  + [ ] VT(F, ps, f)
  + [ ] OMP map(F, p, f=h1)
  + [ ] OMP save(F, p, f=h1)

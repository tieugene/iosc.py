# Test
## 0.3.4 => 0.3.5

Digits:

- в левом окошке значения сигнала
- указках замера (Measurement poiners)
- указках уровней (Level poiners)
- Tools (векторная диаграма, диаграмма гапомник, таблица значений, OMP map)
- Экспорт в CVS
- Печать в PDF
(итого примерно 9+ цифр)

Цифры зависят от:

- несмещенный/центрированный сигнал (поэтому лучше взять осциллограмму с чувствиетльным смещением)
- первичный/вторичный (поэтому надо взять ...му с первичными и вторичными сигналами)
- значением "View as" (термин пока не определен)
(итого пока 2x2x8=32 комбинации)
- положения указателей, естественно
- совмещение сигналов

### `h1_h.cfg.comtrade`
- Center: ok
- ViewAs: ok
- PorS: err (~~223.699 A~~ 26.844 kA) == &times;120

#### Try 1: PorS &cross;
##### Data:
- Signal:
  + id: Ib:
  + uu: A
  + a: 0.01726075
  + p: 600
  + s: 5
  + pors: S
- pos: 1
- v: -44
- S:
  + calc: -0,759473 A
  + .3.4: -759.473 mA
  + .3.5: -759.473 mA
- P:
  + calc:
  + .3.4: -91.137 A (&times;120)
  + .3.5: -10.936 kA (**&times;120**)

##### Calls:
- [ ] AnalogSignalLabel.slot_update_value()
- [ ] &rdsh;ASignalLabel.__value_str
- [ ] &rdsh;ASignalSuit.sig2str_i(self.ss.bar.table.oscwin.main_ptr_i)
- [ ] &rdsh;ASignal.as_str_full(ASignal.value(i, cnt, pors), pors)
- [ ] &rdsh;ASignal.as_str(pors)

#### Try 2: Mid, Eff &cross;
#### Try 3:
- LvlPtr PorS &cross;
- ValueTable lies
- CVD segfault
- HD segfault

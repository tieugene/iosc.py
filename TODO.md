# TODO

## 0.3.6: OMP, ru, styling
- [ ] #152 ~~, #153~~ Механизм управления указками ОМП
- [ ] #258, #259 Руссификация интерфейса
- [ ] #260 Включение возможности изменения стиля Qt приложения

### OMP:
- [x] ptrs in samples
- [x] Limit:
  + [x] osc must be -2T..T
  + [x] or:
    * [x] warning window
    * [x] OMP ptrs disabled
    * [x] "OMP map" disabled
    * [x] "OMP save" disabled
- [x] Initial positions: PD=-T, SC=+T
- [ ] Moves:
  + [ ] PD=t<sub>min</sub>..t&#8320;-1, by SC
  + [ ] SC=T..t<sub>max</sub>
- [ ] Chg (on 2-click):
  - 2..10 (T)
  - increase:
    + SC moves right
    + if &gt; t<sub>max</sub> => t<sub>max</sub> and
    + PD moves left
  - decrease:
    + SC moves left
    + if &lt; T => T and
    + PD moves right
- [ ] Save/restore

## 0.3.7: Deploy
- [ ] Доработка/тестирование на версиях:
  + Windows: 7-11 x64
  + Fedora Linux 36/37 x64 rpm dynamic
  + Ubuntu Linux 22.04/22.10 x64 deb dynamic
- [ ] Разработка установщиков:
  + Windows 7, 8, 8.1, 10, 11 x64 установщик *.exe;
  + Fedora Linux 36/37 x64 rpm dynamic
  + Ubuntu Linux 22.04/22.10 x64 deb dynamic.

## x.y.z. Calculated signals
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

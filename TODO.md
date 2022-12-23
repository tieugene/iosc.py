# TODO

Current job: [0.3.3. Misc](https://github.com/tieugene/iosc.py/milestone/15)

- [ ] 2.3.3.5. Cfg load

## Current:
- [x] ver:str
- [x] Bar:
  + [x] Signals:
    - [x] Show:bool
    - [x] color:rgb
    - [x] style:enum
    - [x] MsrPtrs:&Xi;[]
    - [x] LvlPtrs:float[] *(%)*
  + [x] Height:int
  + [x] Y-zoom:int
  + [ ] ~Y-position:?~
- [x] Osc window:
  + [x] X-zoom:int
  + [ ] ~Width:int~
  + [ ] ~Col1 widths:int~
  + [ ] ~X-position:?~
- [x] Mode:
  + [x] PorS:bool
  + [x] ViewAs:enum
  + [x] Shifted/Y-centered:bool
- [ ] Ptr positions:
  + [x] MainPtr:&xi;
  + [x] SC ptrs:(&Xi;, width:int)
  + [ ] TmpPtrs:&Xi;[]
- [ ] Tools:
  + [ ] CVD:
    - [ ] Show:bool
    - [ ] Base:int
    - [ ] Used:int[]
  + [ ] HD:
    - [ ] Show:bool
    - [ ] Used:int[]
  + [ ] OMP:
    - [ ] Show:bool
    - [ ] Used:int[6]
- [ ] ~CRC~:
  - [ ] A-sigs:int
  - [ ] B-sigs:int
  - [ ] Samples:int
  - [ ] Rate:int (!)
  - [ ] iz:&Xi;

## Ideas:

Detach signals + recreate bars:

- Bars:
  1. collect and detach all SS'
  2. delete all bars
  3. add bar and attach SSs
- Not bars:
  + B4 SS'
  + AftR SS'

# TODO

Current job: [0.3.3. Misc](https://github.com/tieugene/iosc.py/milestone/15)

- [ ] 2.3.3.5. Cfg load

## Current:
- [x] ver:str
- [ ] Osc window:
  + [ ] X-zoom:int
  + [ ] ~Width:int~
  + [ ] ~Col1 widths:int~
  + [ ] ~X-position:?~
- [ ] Mode:
  + [ ] PorS:bool
  + [ ] ViewAs:enum
  + [ ] Shifted/Y-centered:bool
- [ ] Ptr positions:
  + [ ] MainPtr:&xi;
  + [ ] SC ptrs:(&Xi;, width:int)
  + [ ] TmpPtrs:&Xi;[]
- [ ] Bar *(in tables)*:
  + [x] Signals:
    - [ ] Show:bool
    - [ ] *color:rgb*
    - [ ] *style:enum*
    - [ ] MsrPtrs:&Xi;[]
    - [ ] LvlPtrs:float[] *(%)*
  + [ ] Height:int (px, A-sig)
  + [ ] Y-zoom:int
  + [ ] ~Y-position:?~
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

- ~~delete and reload bars and signals~~
- detach signals + recreate bars:
  1. collect and detach all SS'
  2. delete all bars
  3. add bar and attach SSs
- Not bars:
  + B4 SS'
  + AftR SS'

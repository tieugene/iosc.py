# TODO

Current job: [0.3.0](https://github.com/tieugene/iosc.py/milestone/12)

## FIXME:

- […] DnD: Clean/Restore MsrPtr/LvlPtr:
  + ?Store ptrs
  + del ptrs
  + detach
  + embed
  + create ptrs
- [ ] Y-zoom unstable (w/ scroll)
- [ ] Bar height (init, hide, DnD)
- [ ] Y-zoom: reset for exact status-only bar
- [ ] X-resize: too slow
- [ ] File - Close

## Done
- [x] z-ptr (bottom)
- [x] Signal: color, style
- [x] Scale:
  + [x] X:
    * [x] scroll
    * [x] resize *(дергается)*
    * [x] zoom
  + [x] Y:
    * [x] resize
    * [x] resize_all
    * [x] zoom *(unstable)*
    * [x] scroll
- [x] ContextMenu:
  + [x] prop
  + [x] hide
- [x] DnD:
  + [x] sig.join
  + [x] sig.move
  + [x] sig.unjoin
  + [x] bar.move
- [x] Switch:
  + [x] pors
  + [x] shift
  + [x] viewas
- [x] Pointers:
  + [x] Common:
    + [x] Main
    + [x] OMP
    + [x] Tmp
  + [x] Analog:
    * [x] Msr
    * [x] Lvl
- [x] Fixes:
  + [x] Plot: Signal normalize
  + [x] SignalLabelList: deselect
  + [x] Scatters (none/plus)
  + [x] MainPtr move labels refresh
  + [x] Chk shift (rerange)
  + [x] Disable Y-scaling (zoom/resize[_all]) for status-only bars
  + [x] Y-zoom indicator

## Samples:

- `IMF3R-7783--13-03-11-15-19-07.cfg`:
  + Samples: 120
  + Freq: 50 Hz
  + Rate: 600 Hz
  + SPP: 12
  + Sample width, ms: 1.(6)
  + Z-point: &numero;49

## Local Ptrs:

- MsrPtr:
  + uid (!)
  + i (position)
  + func_i
- LvlPtr:
  + uid (!)
  + y

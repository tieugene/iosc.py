# Done

## Ptr behaviour

- On Item.mousePressed: select
- On Item.mouseMove: __move
- On Item.mouseReleased: deselect

## OMP ptrs
- SC:
  + Init: Z+2T
  + Allways > Z
  + Movable
  + Stop on tics only
  + 2-clickable
- PD:
  + Init: Z-T
  + Allways < Z
  + Moving with SC

## Tmp ptrs

Same as MainPtr but:

- other color
- not set by mouse click
- right click (del, change)

Behavior:

- Add:
  + root: mk new idx
  + &forall; chart: mk new TmpPtr
- Move:
  + as MainPtr
- Del:
  + root: rm idx from list
  + &forall; chart: rm TmpPtr

- [x] Add, __move
  - [x] Chart
  - [x] Top
  - [x] Bottom
- [x] Context menu
- [x] Del
- [x] Edit (value, name)

## Msr ptrs

- [x] Select (QListWidget)
- [x] Add, __move (depends on pors/shift/func)
- [x] Context menu
- [x] Del
- [x] Edit (value, func)
- [x] Refresh on pors/shift change
- [x] Color (+refresh)

## Lvl ptrs
- [x] Select
- [x] Add
- [x] Context menu
- [x] Del
- [x] Edit:
  - [x] pors
- [x] Refresh on change:
  + [x] color
  + [x] pors
  + [x] ~~shift~~ (undefined behavior)

## 0.3.0:
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
  + [x] DnD: Clean/Restore MsrPtr/LvlPtr
  + [x] DnD: TmpPtr not restored on signal unjoin
- [x] `ComtradeWidget.__do_file_close()`

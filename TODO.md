# TODO

Current job: [Msr ptrs](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#2352-%D0%B7%D0%B0%D0%BC%D0%B5%D1%80%D1%8B)


## Ptr behaviour

- On Item.mousePressed: select
- On Item.mouseMove: move
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

- [x] Add, move
  - [x] Chart
  - [x] Top
  - [x] Bottom
- [x] Context menu
- [x] Del
- [x] Edit (value, name)

## Msr ptrs

- [x] Select (QListWidget)
- [x] Add, move:
  + [x] Analog: depends on pors/shift/func
- [ ] Context menu
- [ ] Del
- [ ] Edit (value, name)
- [ ] AnalogMsrPtr: refresh on pors/shift/func change

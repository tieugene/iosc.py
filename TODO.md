# TODO

Current job: [Lvl ptrs](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#2353-%D1%83%D1%80%D0%BE%D0%B2%D0%B5%D0%BD%D1%8C)


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
- [x] Edit
- [ ] Refresh on change:
  + [x] color
  + [ ] pors
  + [ ] shift

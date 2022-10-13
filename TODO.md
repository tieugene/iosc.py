# TODO

Current job: [Tmp ptrs](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#2351-%D0%B2%D1%80%D0%B5%D0%BC%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F-%D1%83%D0%BA%D0%B0%D0%B7%D0%BA%D0%B0)


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

## Hot:
- Ptr.slot_ptr_move(int)
- Ptr.signal_ptr_moved => root.slot_...

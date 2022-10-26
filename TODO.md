# TODO

Current job: [x-DnD](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#23217-%D0%BF%D0%B5%D1%80%D0%B5%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BE%D0%BA%D0%BD%D0%B0-%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F-%D1%81%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB%D0%B0-%D1%86%D0%B5%D0%BB%D0%B8%D0%BA%D0%BE%D0%BC)

Idea: QListWidget.setItemWidget()

- […] sig unjoin
- [ ] sig_table: deselect on mouse_up
- [ ] semi-transparent draging row
- [ ] *centralized row/sig storage*
- [ ] Bug: v-scale scrollbar absent
- [x] v-zoom
- [x] state/restore
- [x] x-move row
- [x] LvlPtr (-1..1)
- [x] sig join
- [x] sig move
- [x] sig_label: deselect on mouse_up

## DnD:

[rtfm](https://stackoverflow.com/questions/26227885/drag-and-drop-rows-within-qtablewidget)


## MultiChart:

- QCP axis: unified:
  + Max: -1.1…1.1
  + Min: -0.1…0.1
- Graphs:
  + 0: MainPtr, SCPtr, TmpPtr[]
  + 1+: a graph per signal
- Signal ranges:
  + Status: 0…0.(6)  (0.6*1.1)
  + Analog: -1..1 (max)
- v-zoom: ?

## Drop:

no| src | dst |tbl| action
--|-----|-----|---|-------
0 | tbl | B2n | i | ins > cp widgets (!sn++, 2>2..3=x)
1 | tbl | B2n | x | ins > (sv[] > rm > ld[])
4 | tbl | Ovr | i | ~~cp[]~~
5 | tbl | Ovr | x | ~~cp[]~~
2 | sig | B2N | i | ins > cp (sn++, 2>2..3=x)
3 | sig | B2N | x | ins > cp
6 | sig | Ovr | i | cp
7 | sig | Ovr | x | cp

- All adrop actions: mv (or ignore on err)
- On B2n: ins+__apply_row

Stage &numero;2:
- [x] ~~tbl.Ovr~~
- [x] tbl.B2n.i
- [x] tbl.B2n.x
- [ ] sig.Ovr{.i/x}
- [ ] sig.B2n{.i/x}

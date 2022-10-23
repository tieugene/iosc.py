# TODO

Current job: [x-DnD](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#23217-%D0%BF%D0%B5%D1%80%D0%B5%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BE%D0%BA%D0%BD%D0%B0-%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F-%D1%81%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB%D0%B0-%D1%86%D0%B5%D0%BB%D0%B8%D0%BA%D0%BE%D0%BC)

- [ ] Bug: v-scale scrollbar absent
- [ ] ~~Bug: X-scaled not moved correctly~~

## DnD:

[rtfm](https://stackoverflow.com/questions/26227885/drag-and-drop-rows-within-qtablewidget)

## Associations:

- row == csp
- sig = graph

### Ptr:
- Main: row
- OMP: row
- Tmp: row
- Msr: sig
- Lvl: sig

## QCP demo:

- `interactions` - 4 x Graph
- `scrollbar-axis-range-control`: 2 x Graph
- `plots`:
  + 1: setupSimpleDemo: 2x, simple
  + 3: 17x
  + 5: 5x
  + 6: 5x
  + 7: 2x
  + 17: setupAdvancedAxesDemo: 2x, mixed yAxis

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

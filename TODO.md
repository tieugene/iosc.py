# TODO

Current job: [x-DnD](https://github.com/michDaven/AbScan-TechReq/blob/main/asciidoc1.adoc#23217-%D0%BF%D0%B5%D1%80%D0%B5%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BE%D0%BA%D0%BD%D0%B0-%D0%BE%D1%82%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F-%D1%81%D0%B8%D0%B3%D0%BD%D0%B0%D0%BB%D0%B0-%D1%86%D0%B5%D0%BB%D0%B8%D0%BA%D0%BE%D0%BC)

- Idea:
  - i-Move: as is (default + cp widget)
  - x-Move: cp + chg parent + rm row
- Seems cellWidget() cannot be moved between tables because \*ptr.  
- &rdsh; serialize | deserialize
- &rdsh; or copy (like copy constructor)
- ~~$rdsh; copy.[deep]copy~~ (cannot pickle)

## DnD:

SignalListTable.dndDrop() finish:
self/cross &times; None/ignore/accept = 9.

s | x | s | x
---|---|---|---
 n | n | + | segfault
 i | n | + | segfault
 i | i | + | segfault
 i | a | + | segfault
 
Idea: неправильно ты бутерброд ешь, дядя Федор:
- get proposed (event.proposedAction() == `copy`)
- check available (event.possibleActions() == `copy`|`move`)
- set requried (event.setProposedAction(move))
- event.accept()

Seems moving widget between rows doing _after_ old row deleted.
And on x-Move widget is deleting

[rtfm](https://stackoverflow.com/questions/26227885/drag-and-drop-rows-within-qtablewidget)

### Tries
- src_table.removeCellWidget() - clear dst
- x: cp - works, src is empty

## Associations:

- row == csp
- sig = graph

### Ptr:
- Main: row
- OMP: row
- Tmp: row
- Msr: sig
- Lvl: sig

### Misc:
- V-scale: &hellip;


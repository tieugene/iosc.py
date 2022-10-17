# TODO

Current job: x-DnD

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


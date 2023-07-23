#!/usr/bin/sh
D=$(realpath "$(dirname $(realpath $0))/..")
PYTHONPATH="$D" python3 "$D/iosc/mainwindow.py" $@

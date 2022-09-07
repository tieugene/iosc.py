# iosc.py

View/analyze comtrade oscillograms

## Requirements
- [Python3](https://www.python.org/) with
  - [numpy](https://numpy.org/)
  - [chardet](https://github.com/chardet/chardet)
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
  - [QCustomPlot2-PyQt5](https://pypi.org/project/QCustomPlot2/)

## Includes
- [python-comtrade](https://github.com/dparrini/python-comtrade)
- [~~open-iconic~~](https://github.com/iconic/open-iconic) icons

## Installation

1. Download and unpack source tarball
2. Install required dependencies (see below)
3. Run main script: `iosc/main.py`

### OS specific
#### Windows:

1. Download and install [Python3](https://www.python.org/downloads/windows/)
2. Add required python packages (cmd.exe as admin):
   ```shell
   pip install numpy chardet QCustomPlot2
   ```

#### Linux:
```bash
# RH-based (last rpm is hand-made):
dnf install python3-numpy python3-chardet python3-qcustomplot2
# Debian-based:
apt install python3-numpy python3-chardet python3-pyqt5
# TODO: python3-qcustomplot2
```

#### macOS
(with [homebrew](https://brew.sh/)):
```bash
brew install python3
pip3 install numpy chardet QCustomPlot2
```

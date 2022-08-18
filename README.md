# iosc.py

View/analyze comtrade oscillograms

## Requirements
- Python 3.9+ with
  - PySide2
  - numpy
  - chardet

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
   pip install PySide2 numpy chardet
   ```

#### Linux:
```bash
# RH-based:
dnf install python3-pyside2 python3-numpy python3-chardet
# Debian-based:
apt install python3-numpy python3-chardet python3-pyside2.qtcharts
```

#### macOS
(with [homebrew](https://brew.sh/)):
```bash
brew install python3
pip3 install PySide2 numpy chardet
```

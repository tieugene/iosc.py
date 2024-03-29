# iosc.py

View/analyze comtrade oscillograms

## Requirements:
- [Python3](https://www.python.org/) &ge; 3.9 with
  - [numpy](https://numpy.org/)
  - [chardet](https://github.com/chardet/chardet)
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
  - [QCustomPlot-PyQt5](https://pypi.org/project/QCustomPlot-PyQt5/):
     * Fedora: out from box
     * Debian-based: [OBS repo](https://build.opensuse.org/package/show/home:sergeyopensuse:gpxviewer/python-qcustomplot-pyqt)
     * Windows: `pip`

### Bundled:
- [python-comtrade](https://github.com/dparrini/python-comtrade)
- [~~open-iconic~~](https://github.com/iconic/open-iconic) icons

## Installation:
### Fedora:

```sh
sudo dnf install iosc-...noarch.rpm
```

### Debian-based:

```sh
# from OBS repo above
sudo apt install https://...python3-qcustomplot-pyqt5_...amd64.deb
sudo apt install iosc_..._all.deb
```

## Packaging:

### Fedora:

```sh
rpmbuild -ta iosc-<version>.tar.gz
```

### Debian-based:

```sh
tar xf iosc-<version>.tar.gz && cd iosc-<version> && dpkg-buildpackage
```

### Windows:

```sh
# 1. install python
# 2. install requirements
pip install numpy chardet pyqt5 QCustomPlot_PyQt5 pyinstaller
# 3. install iosc itself (in folder with unpacked sources):
pip install .
# 4. build
pyinstaller -y -w -F -n iosc-<version> contrib/win.py
```

## Run from sources:

1. Download and unpack source tarball
2. Install required dependencies (see below)
3. Run main script: `PYTHONPATH="..." iosc/mainwindow.py`

### OS specific
#### Windows:

1. Download and install [Python3](https://www.python.org/downloads/windows/)
2. then:

```cmd
pip install numpy chardet pyqt5 QCustomPlot_PyQt5
pip install .
pythonw.exe -c "from iosc.mqinwindow import main; main()"
```

#### Linux:
##### Fedora:

```sh
dnf install python3-numpy python3-chardet python3-qcustomplot-pyqt5
```

##### Debian-based:

```sh
apt install python3-numpy python3-chardet python3-pyqt5
# see above
apt install https://...python3-qcustomplot-pyqt5_...amd64.deb
```

#### ~~macOS~~

(with [homebrew](https://brew.sh/)):

```sh
brew install python3
pip3 install numpy chardet
```

&hellip; and install `QCustomPlot_PyQt5` according to [documentation](https://github.com/salsergey/QCustomPlot-PyQt#macos).

## [Specification](https://github.com/michDaven/AbScan-TechReq)
0.3.7
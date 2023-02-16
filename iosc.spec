Name:		iosc
Version:	0.3.5
Release:	1%{?dist}
License:	GLPv3
Summary:	Comtrade viewer
URL:		https://github.com/tieugene/iosc.py
Source0:	%{url}/archive/refs/tags/%{version}.tar.gz#/iosc.py-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:  pyproject-rpm-macros
# python3-wheel
BuildRequires:	%{py3_dist wheel}
# python3-numpy
BuildRequires:	%{py3_dist numpy}
# python3-chardet
BuildRequires:	%{py3_dist chardet}
# python3-qcustomplot-pyqt5
BuildRequires:	%{py3_dist qcustomplot-pyqt5}

%description
%{summary}.


%prep
%autosetup -n iosc.py-%{version}
%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files %{name}


%files
%doc README.md
%license LICENSE
%{_bindir}/%{name}


%changelog
* Thu Feb 16 2023 TI_Eugene <ti.eugene@gmail.com> - 0.3.5-1
- Initial packaging

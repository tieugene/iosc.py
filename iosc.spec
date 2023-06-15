Name:		iosc
Version:	0.3.7
Release:	rc2%{?dist}
License:	GLPv3
Summary:	Comtrade viewer
URL:		https://github.com/tieugene/iosc.py
Source0:	%{url}/archive/refs/tags/%{version}.tar.gz#/iosc.py-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	pyproject-rpm-macros
# python3-wheel
BuildRequires:	%{py3_dist wheel}
# python3-numpy
BuildRequires:	%{py3_dist numpy}
# python3-chardet
BuildRequires:	%{py3_dist chardet}
# python3-qcustomplot-pyqt5
BuildRequires:	%{py3_dist qcustomplot-pyqt5}
BuildRequires:	desktop-file-utils
# python3-devel
# BuildRequires:	pkgconfig(python)
# python3-pip
# BuildRequires:	%%{py3_dist pip)

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
desktop-file-install contrib/%{name}.desktop


%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop


%files -f %{pyproject_files}
%doc README.md
%license LICENSE
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop


%changelog
* Mon Jun 05 2023 TI_Eugene <ti.eugene@gmail.com> - 0.3.7-rc1
- Windows compliant
- Styling off
- i18n qrc'ed

* Sun Jun 04 2023 TI_Eugene <ti.eugene@gmail.com> - 0.3.6-2
- Debian compliant

* Wed Apr 05 2023 TI_Eugene <ti.eugene@gmail.com> - 0.3.6-1
- Version bump

* Thu Feb 16 2023 TI_Eugene <ti.eugene@gmail.com> - 0.3.5-1
- Initial packaging

# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           rpkg
Version:        1.0
Release:        1%{?dist}
Summary:        Utility for interacting with rpm+git packaging systems

Group:          Applications/System
License:        GPLv2+
URL:            https://fedorahosted.org/rpkg
Source0:        https://fedorahosted.org/releases/r/p/rpkg/rpkg-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires:       python-argparse
Requires:       pyrpkg => %{name}-%{version}

BuildArch:      noarch
BuildRequires:  python-devel, python-setuptools
# We br these things for man page generation due to imports
BuildRequires:  GitPython, koji, python-pycurl
%if 0%{?rhel} == 5 || 0%{?rhel} == 4
BuildRequires:  python-hashlib
BuildRequires:  python-argparse
%endif

%description
A tool for managing RPM package sources in a git repository.

%package -n pyrpkg
Summary:        Python library for interacting with rpm+git
Group:          Applications/Databases
Requires:       GitPython >= 0.2.0, python-argparse
Requires:       python-pycurl, koji
Requires:       rpm-build, rpm-python
Requires:       rpmlint, mock, curl, openssh-clients, redhat-rpm-config
%if 0%{?rhel} == 5 || 0%{?rhel} == 4
Requires:       python-kitchen
Requires:       python-hashlib
%endif

%description -n pyrpkg
A python library for managing RPM package sources in a git repository.


%prep
%setup -q


%build
%{__python} setup.py build
%{__python} src/rpkg_man_page.py > rpkg.1


%install
#rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
%{__install} -d $RPM_BUILD_ROOT%{_mandir}/man1
%{__install} -p -m 0644 rpkg.1 $RPM_BUILD_ROOT%{_mandir}/man1

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/rpkg
%{_sysconfdir}/bash_completion.d
%{_bindir}/%{name}
%{_mandir}/*/*

%files -n pyrpkg
%doc COPYING README
# For noarch packages: sitelib
%{python_sitelib}/*


%changelog
* Tue Jun 14 2011 Jesse Keating <jkeating@redhat.com> - 1.0-1
- Initial package

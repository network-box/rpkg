# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           rpkg
Version:        1.19
Release:        1%{?dist}
Summary:        Utility for interacting with rpm+git packaging systems

Group:          Applications/System
License:        GPLv2+ and LGPLv2
URL:            https://fedorahosted.org/rpkg
Source0:        https://fedorahosted.org/releases/r/p/rpkg/rpkg-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires:       python-argparse
Requires:       pyrpkg => %{name}-%{version}

# Use this to force plugins to update
Conflicts:      fedpkg <= 1.7

BuildArch:      noarch
BuildRequires:  python-devel, python-setuptools
# We br these things for man page generation due to imports
BuildRequires:  GitPython, koji, python-pycurl
BuildRequires:  python-hashlib
BuildRequires:  python-argparse
BuildRequires:  python-kitchen

%description
A tool for managing RPM package sources in a git repository.

%package -n pyrpkg
Summary:        Python library for interacting with rpm+git
Group:          Applications/Databases
Requires:       GitPython >= 0.2.0, python-argparse
Requires:       python-pycurl, koji
Requires:       rpm-build, rpm-python
Requires:       rpmlint, mock, curl, openssh-clients, redhat-rpm-config
Requires:       python-kitchen
Requires:       python-hashlib

%description -n pyrpkg
A python library for managing RPM package sources in a git repository.


%prep
%setup -q


%build
%{__python} setup.py build
%{__python} src/rpkg_man_page.py > rpkg.1


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
%{__install} -d $RPM_BUILD_ROOT%{_mandir}/man1
%{__install} -p -m 0644 rpkg.1 $RPM_BUILD_ROOT%{_mandir}/man1

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%config(noreplace) %{_sysconfdir}/rpkg
%{_sysconfdir}/bash_completion.d
%{_bindir}/%{name}
%{_mandir}/*/*

%files -n pyrpkg
%doc COPYING COPYING-koji LGPL README
# For noarch packages: sitelib
%{python_sitelib}/pyrpkg
%{python_sitelib}/rpkg-%{version}-py?.?.egg-info


%changelog
* Tue Dec 11 2012 Pavol Babincak <pbabinca@redhat.com> - 1.19-1
- Generate mock-config for mockbuild if needed (rhbz#856928) (pbabinca)

* Mon Apr 16 2012 Jesse Keating <jkeating@redhat.com> - 1.18-1
- Use rpmdefines when querying for package name

* Mon Apr 09 2012 Jesse Keating <jkeating@redhat.com> - 1.17-1
- Don't assume master branch for chain builds (jkeating)

* Mon Mar 26 2012 Jesse Keating <jkeating@redhat.com> - 1.16-1
- Only read from .koji/config (jkeating)

* Wed Mar 21 2012 Jesse Keating <jkeating@redhat.com> - 1.15-1
- Fix branch push warning (jkeating)
- Handle CVS based builds when getting build hash (jkeating)

* Mon Mar 12 2012 Jesse Keating <jkeating@redhat.com> - 1.14-1
- Warn if the checked out branch cannot be pushed (jkeating)
- Warn if commit or tag fails and we don't push (#21) (jkeating)
- Honor ~/.koji/config (rhbz#785776) (jkeating)
- Update help output for switch-branch (rhbz#741742) (jkeating)

* Thu Mar 01 2012 Jesse Keating <jkeating@redhat.com> - 1.13-1
- Return proper exit code from builds (#20) (jkeating)
- Fix md5 option in the build parser (jkeating)
- More completion fixes (jkeating)
- Add mock-config and mockbuild completion (jkeating)
- Simplify test for rpkg availability. (ville.skytta)
- Fix ~/... path completion. (ville.skytta (jkeating)
- Add a --raw option to clog (#15) (jkeating)
- Make things quiet when possible (jkeating)
- Fix up figuring out srpm hash type (jkeating)
- Allow defining an alternative builddir (jkeating)
- Conflict with older fedpkg (jkeating)
- Attempt to automatically set the md5 flag (jkeating)
- Use -C not -c for config.  (#752411) (jkeating)
- Don't check gpg sigs when importing srpms (ticket #16) (jkeating)
- Enable md5 option in mockbuild (twaugh) (jkeating)

* Tue Jan 24 2012 Jesse Keating <jkeating@redhat.com> - 1.12-1
- Fix mock-config (ticket #13) (jkeating)
- Make md5 a common build argument (jkeating)
- Move arches to be a common build argument (ticket #3) (jkeating)
- Find remote branch to track better (jkeating)

* Fri Jan 13 2012 Jesse Keating <jkeating@redhat.com> - 1.11-1
- Change clog output to be more git-like (sochotnicky)
- Fix mockconfig property (bochecha)
- Use only new-style classes everywhere. (bochecha)
- Testing for access before opening a file is unsafe (bochecha)
- Add a gitbuildhash command (jkeating)
- Always make sure you have a absolute path (aj) (jkeating)
- don't try to import brew, just do koji (jkeating)

* Mon Nov 21 2011 Jesse Keating <jkeating@redhat.com> - 1.10-1
- Use -C for --config shortcut (jkeating)
- Don't leave a directory on failure (#754082) (jkeating)
- Fix chain build (#754189) (jkeating)
- Don't hardcode brew here (jkeating)

* Mon Nov 07 2011 Jesse Keating <jkeating@redhat.com> - 1.9-1
- Don't upload if there is nothing to upload. (jkeating)
- --branch option for import is not supported yet (jkeating)
- Add epilog about mock-config generation (jkeating)
- Don't assume we can create a folder named after the module. (bochecha)
- Fix passing the optional mock root to mockbuild (bochecha)
- Add missing registration for mockbuild target (bochecha)
- Make the clean target work with --path. (bochecha)
- Fix typo in a comment. (bochecha)
- Fix syntax error in main script. (bochecha)
- Fix typo. (bochecha)

* Fri Oct 28 2011 Jesse Keating <jkeating@redhat.com> - 1.8-1
- Get more detailed error output from lookaside (jkeating)
- Move the curl call out to it's own function (jkeating)
- Hide build_common from help/usage (jkeating)
- Fix the help command (jkeating)

* Tue Oct 25 2011 Jesse Keating <jkeating@redhat.com> - 1.7-1
- Support a manually specified mock root (jkeating)
- Add a mock-config subcommand (jkeating)
- Fix a traceback on error. (jkeating)
- Remove debugging code (jkeating)
- More git api updates (jkeating)
- Add topurl as a koji config and property (jkeating)
- Add a mockconfig property (jkeating)
- Turn the latest commit into a property (jkeating)

* Tue Sep 20 2011 Jesse Keating <jkeating@redhat.com> - 1.6-1
- Allow name property to load by itself (jkeating)

* Mon Sep 19 2011 Jesse Keating <jkeating@redhat.com> - 1.5-1
- Fix tag listing (#717528) (jkeating)
- Revamp n-v-r property loading (#721389) (jkeating)
- Don't use os.getlogin (jkeating)
- Code style changes (jkeating)
- Allow fedpkg lint to be configurable and to check spec file. (pingou)
- Handle non-scratch srpm builds better (jkeating)

* Wed Aug 17 2011 Jesse Keating <jkeating@redhat.com> - 1.4-1
- Be more generic when no spec file is found (jkeating)
- Hint about use of git status when dirty (jkeating)
- Don't use print when we can log.info it (jkeating)
- Don't exit from a library (jkeating)
- Do the rpm query in our module path (jkeating)
- Use git's native ability to checkout a branch (jkeating)
- Use keyword arg with clone (jkeating)
- Allow the on-demand generation of an srpm (jkeating)
- Fix up exit codes (jkeating)

* Mon Aug 01 2011 Jesse Keating <jkeating@redhat.com> - 1.3-1
- Fix a debug string (jkeating)
- Set the right property (jkeating)
- Make sure we have a default hashtype (jkeating)
- Use underscore for the dist tag (jkeating)
- Fix the kojiweburl property (jkeating)

* Wed Jul 20 2011 Jesse Keating <jkeating@redhat.com> - 1.2-1
- Fill out the krb_creds function (jkeating)
- Fix the log message (jkeating)
- site_setup is no longer needed (jkeating)
- Remove some rhtisms (jkeating)
- Wire up the patch command in client code (jkeating)
- Add a patch command (jkeating)

* Fri Jun 17 2011 Jesse Keating <jkeating@redhat.com> - 1.1-2
- Use version macro in files

* Fri Jun 17 2011 Jesse Keating <jkeating@redhat.com> - 1.1-1
- New tarball release with correct license files

* Fri Jun 17 2011 Jesse Keating <jkeating@redhat.com> - 1.0-2
- Fix up things found in review

* Tue Jun 14 2011 Jesse Keating <jkeating@redhat.com> - 1.0-1
- Initial package

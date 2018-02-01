%define release 0.1
%define pkg_name aos-toolbox
%define _unpackaged_files_terminate_build 0

Name: %{pkg_name}
Summary: Aruba Networks Toolbox
Group: System Environment/Daemons
URL: http://www.arubanetworks.com/
Version: %{version}
Release: %{release}
Vendor: Aruba Networks
Requires: bash
AutoReqProv: no

License: GPL
Source: %{pkg_name}.tgz
Buildroot: /tmp/${pkg_name}

%description
Toolbox for aos package.

%prep

%install
basedir=/usr/local/aos

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/aos
install__ 0755 build/aosb
install__ 0755 build/aosicp

install__ 0755 pylib/system/shell.py
install__ 0755 pylib/system/string_ext.py
install__ 0755 pylib/wlan/wlan_controller.py

install__ 0755 tools/7z2soscore
install__ 0755 tools/aos-telnet
install__ 0755 tools/sos-crash-debug
install__ 0755 tools/sos-crash-tech-support
install__ 0755 tools/sos-startupscript

%clean

%files
%defattr(-,root,root)
/usr/local/aos/build/aosb
/usr/local/aos/build/aosicp

/usr/local/aos/pylib/system/shell.py
/usr/local/aos/pylib/system/string_ext.py
/usr/local/aos/pylib/wlan/wlan_controller.py

/usr/local/aos/tools/7z2soscore
/usr/local/aos/tools/aos-telnet
/usr/local/aos/tools/sos-crash-debug
/usr/local/aos/tools/sos-crash-tech-support
/usr/local/aos/tools/sos-startupscript

%pre

%post

%preun
rm -rf /usr/local/aos
exit 0

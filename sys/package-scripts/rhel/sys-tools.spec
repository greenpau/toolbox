%define release 0.1
%define pkg_name sys-tools
%define _unpackaged_files_terminate_build 0

Name: %{pkg_name}
Summary: System Utility Toolbox
Group: System Environment/Daemons
URL: http://www.github.com/
Version: %{version}
Release: %{release}
Vendor: Sabyasachi Sengupta
Requires: bash

License: GPL
Source: %{pkg_name}.tgz
Buildroot: /tmp/${pkg_name}

%description
Toolbox for System Tools

%prep

%install
basedir=/usr/local/sys-tools

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT $basedir
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/sys/tools
install__ 0755 bsall
install__ 0755 bscope
install__ 0755 scope
install__ 0755 sync-host-date
install__ 0755 tree


%clean

%files
%defattr(-,root,root)
/usr/local/sys-tools/bsall
/usr/local/sys-tools/bscope
/usr/local/sys-tools/scope
/usr/local/sys-tools/sync-host-date
/usr/local/sys-tools/tree

%pre

%post

%preun
rm -rf /usr/local/sys-tools
exit 0

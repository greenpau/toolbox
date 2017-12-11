%define release 0.1
%define pkg_name p4-tools
%define _unpackaged_files_terminate_build 0

Name: %{pkg_name}
Summary: p4 wrapper tools
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
Toolbox for p4 (perforce wrappers)

%prep

%install
basedir=/usr/local/p4

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT $basedir
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/p4
install__ 0755 tools/pentervw
install__ 0755 tools/plsvw
install__ 0755 tools/ppwvw

%clean

%files
%defattr(-,root,root)
/usr/local/p4/tools/pentervw
/usr/local/p4/plsvw
/usr/local/p4/tools/ppwvw

%pre

%post

%preun
rm -rf /usr/local/p4
exit 0
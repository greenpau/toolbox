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
basedir=/usr/local/p4-tools

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/p4/tools
install__ 0755 libp4.sh
install__ 0755 panot
install__ 0755 pdiffvw
install__ 0755 pentervw
install__ 0755 plsvw
install__ 0755 plogvw
install__ 0755 pman
install__ 0755 pmkvw
install__ 0755 ppwvw
install__ 0755 preview
install__ 0755 pstatvw

%clean

%files
%defattr(-,root,root)
/usr/local/p4-tools/libp4.sh
/usr/local/p4-tools/panot
/usr/local/p4-tools/pdiffvw
/usr/local/p4-tools/pentervw
/usr/local/p4-tools/plsvw
/usr/local/p4-tools/plogvw
/usr/local/p4-tools/pman
/usr/local/p4-tools/pmkvw
/usr/local/p4-tools/ppwvw
/usr/local/p4-tools/preview
/usr/local/p4-tools/pstatvw

%pre

%post

%preun
rm -rf /usr/local/p4-tools
exit 0

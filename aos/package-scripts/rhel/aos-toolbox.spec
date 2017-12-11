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

rm -rf $RPM_BUILD_ROOT $basedir
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/aos
install__ 0755 build/aosb

%clean

%files
%defattr(-,root,root)
/usr/local/aos/build/aosb

%pre

%post

%preun
rm -rf /usr/local/aos
exit 0
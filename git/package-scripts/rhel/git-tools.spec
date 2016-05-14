%define release 0.1
%define pkg_name git-tools
%define _unpackaged_files_terminate_build 0

Name: %{pkg_name}
Summary: Git Wrapper Toolbox
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
Toolbox for Git Tools

%prep

%install
basedir=/usr/local/git-tools

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT $basedir
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/git/tools
install__ 0755 grmsb
install__ 0755 gmv
install__ 0755 gpull
install__ 0755 gshow
install__ 0755 gdiff
install__ 0755 glsbr
install__ 0755 glspush
install__ 0755 gco
install__ 0755 gadd
install__ 0755 gpwsb
install__ 0755 gbrstart
install__ 0755 gapply-rev
install__ 0755 glssb
install__ 0755 grm
install__ 0755 gentersb
install__ 0755 glog
install__ 0755 gci
install__ 0755 gstash
install__ 0755 gmksb
install__ 0755 gfetch
install__ 0755 gmkbr
install__ 0755 gcherry-pick
install__ 0755 gpush
install__ 0755 gstat
install__ 0755 libgit.sh


%clean

%files
%defattr(-,root,root)
/usr/local/git-tools/grmsb
/usr/local/git-tools/gmv
/usr/local/git-tools/gpull
/usr/local/git-tools/gshow
/usr/local/git-tools/gdiff
/usr/local/git-tools/glsbr
/usr/local/git-tools/glspush
/usr/local/git-tools/gco
/usr/local/git-tools/gadd
/usr/local/git-tools/gpwsb
/usr/local/git-tools/gbrstart
/usr/local/git-tools/gapply-rev
/usr/local/git-tools/glssb
/usr/local/git-tools/grm
/usr/local/git-tools/gentersb
/usr/local/git-tools/glog
/usr/local/git-tools/gci
/usr/local/git-tools/gstash
/usr/local/git-tools/gmksb
/usr/local/git-tools/gfetch
/usr/local/git-tools/gmkbr
/usr/local/git-tools/gcherry-pick
/usr/local/git-tools/gpush
/usr/local/git-tools/gstat
/usr/local/git-tools/libgit.sh

%pre

%post

%preun
rm -rf /usr/local/git-tools
exit 0

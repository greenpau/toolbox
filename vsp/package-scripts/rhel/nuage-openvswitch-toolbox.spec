%define release 0.1
%define pkg_name nuage-openvswitch-toolbox
%define _unpackaged_files_terminate_build 0

Name: %{pkg_name}
Summary: Nuage Networks Open vSwitch Toolbox
Group: System Environment/Daemons
URL: http://www.openvswitch.org/
Version: %{version}
Release: %{release}
Vendor: Nuage Networks
Requires: bash

License: GPL
Source: %{pkg_name}.tgz
Buildroot: /tmp/${pkg_name}

%description
Toolbox for nuage-openvswitch package.

%prep

%install
basedir=/usr/local/openvswitch

install__() {
    mode=$1
    src=$2
    dst_dir=$RPM_BUILD_ROOT/$basedir/`dirname $src`
    mkdir -p $dst_dir
    install -D -m $mode $src $dst_dir
}

rm -rf $RPM_BUILD_ROOT $basedir
mkdir -p $RPM_BUILD_ROOT $basedir

cd %{pkg_name}/vsp
install__ 0755 pylib/system/logger.py 
install__ 0755 pylib/system/cd.py
install__ 0755 pylib/system/cpu.py
install__ 0755 pylib/system/net.py
install__ 0755 pylib/system/process.py
install__ 0755 pylib/system/shell.py

install__ 0755 pylib/vca/vca_helper.py
install__ 0755 pylib/vca/vca_vrf.py
install__ 0755 pylib/vca/vca_flows.py
install__ 0755 pylib/vca/vca_vm.py
install__ 0755 pylib/vca/vca_evpn_dhcp.py
install__ 0755 pylib/vca/vca_evpn.py
install__ 0755 pylib/vca/vca_pbm.py
install__ 0755 pylib/vca/vca_vpm.py
install__ 0755 pylib/vca/vca_dyn.py
install__ 0755 pylib/vca/vca_mirror.py
install__ 0755 pylib/vca/vca_test.py

install__ 0755 pylib/ovs/ovs_flows.py
install__ 0755 pylib/ovs/ovs_dpdk_vendor_nicira.py
install__ 0755 pylib/ovs/ovs_ofproto.py
install__ 0755 pylib/ovs/ovs_vport_tnl.py
install__ 0755 pylib/ovs/ovs_vport_tap.py
install__ 0755 pylib/ovs/ovs_dpdk_vendor_01org.py
install__ 0755 pylib/ovs/ovs_bridge.py
install__ 0755 pylib/ovs/ovs_dpdk_vendor.py
install__ 0755 pylib/ovs/ovs_dpdk_vendor_switch.py
install__ 0755 pylib/ovs/ovs_helper.py

install__ 0755 pylib/dpdk/dpdk_dev.py
install__ 0755 pylib/dpdk/dpdk_sys.py
install__ 0755 pylib/dpdk/dpdk_helper.py

install__ 0755 pylib/regress/regress.py
install__ 0755 pylib/regress/regular.py
install__ 0755 pylib/regress/express.py
install__ 0755 pylib/regress/quick.py

install__ 0755 templates/vm.xml

install__ 0755 tools/dpdk/dpdk.py
install__ 0755 tools/ovs/ovs-flow-create.py
install__ 0755 tools/ovs/ovs-vport-tap-create.py
install__ 0755 tools/ovs/ovs-tnl-create-many.py
install__ 0755 tools/ovs/ovs-flow-dump.py
install__ 0755 tools/ovs/ovs-vport-tnl-create-l2.py
install__ 0755 tools/ovs/ovs-switch-cleanup.py
install__ 0755 tools/ovs/ovs-switch-status.py
install__ 0755 tools/vca/vca-switch-status.py
install__ 0755 tools/vca/vca-mirror-tests.py
install__ 0755 tools/vca/vca-vport-tap-vrf-tnl-create.py
install__ 0755 tools/vca/vca-vm-start.sh
install__ 0755 tools/vca/dpdk-reinstall-bin-cfg-static
install__ 0755 tools/vca/dpdk-reinstall-bin-cfg-dhcp
install__ 0755 tools/vca/dpdk-reprogram-ovs-flows
install__ 0755 tools/vca/check-port-tp
install__ 0755 tools/vca/iperf-run
install__ 0755 tools/regress/run_regress.py
install__ 0755 tools/system/reinstall-packages
install__ 0755 tools/system/update-ovs-vswitchd
install__ 0755 tools/system/scattach

install__ 0755 third-party/bin/iperf


%clean

%files
%defattr(-,root,root)
/usr/local/openvswitch/pylib/system/logger.py
/usr/local/openvswitch/pylib/system/cd.py
/usr/local/openvswitch/pylib/system/cpu.py
/usr/local/openvswitch/pylib/system/net.py
/usr/local/openvswitch/pylib/system/process.py
/usr/local/openvswitch/pylib/system/shell.py

/usr/local/openvswitch/pylib/vca/vca_helper.py
/usr/local/openvswitch/pylib/vca/vca_vrf.py
/usr/local/openvswitch/pylib/vca/vca_flows.py
/usr/local/openvswitch/pylib/vca/vca_vm.py
/usr/local/openvswitch/pylib/vca/vca_evpn_dhcp.py
/usr/local/openvswitch/pylib/vca/vca_evpn.py
/usr/local/openvswitch/pylib/vca/vca_pbm.py
/usr/local/openvswitch/pylib/vca/vca_vpm.py
/usr/local/openvswitch/pylib/vca/vca_dyn.py
/usr/local/openvswitch/pylib/vca/vca_mirror.py
/usr/local/openvswitch/pylib/vca/vca_test.py

/usr/local/openvswitch/pylib/ovs/ovs_flows.py
/usr/local/openvswitch/pylib/ovs/ovs_dpdk_vendor_nicira.py
/usr/local/openvswitch/pylib/ovs/ovs_ofproto.py
/usr/local/openvswitch/pylib/ovs/ovs_vport_tnl.py
/usr/local/openvswitch/pylib/ovs/ovs_vport_tap.py
/usr/local/openvswitch/pylib/ovs/ovs_dpdk_vendor_01org.py
/usr/local/openvswitch/pylib/ovs/ovs_bridge.py
/usr/local/openvswitch/pylib/ovs/ovs_dpdk_vendor.py
/usr/local/openvswitch/pylib/ovs/ovs_dpdk_vendor_switch.py
/usr/local/openvswitch/pylib/ovs/ovs_helper.py

/usr/local/openvswitch/pylib/dpdk/dpdk_dev.py
/usr/local/openvswitch/pylib/dpdk/dpdk_sys.py
/usr/local/openvswitch/pylib/dpdk/dpdk_helper.py

/usr/local/openvswitch/pylib/regress/regress.py
/usr/local/openvswitch/pylib/regress/regular.py
/usr/local/openvswitch/pylib/regress/express.py
/usr/local/openvswitch/pylib/regress/quick.py

/usr/local/openvswitch/templates/vm.xml

/usr/local/openvswitch/tools/dpdk/dpdk.py
/usr/local/openvswitch/tools/ovs/ovs-flow-create.py
/usr/local/openvswitch/tools/ovs/ovs-vport-tap-create.py
/usr/local/openvswitch/tools/ovs/ovs-tnl-create-many.py
/usr/local/openvswitch/tools/ovs/ovs-flow-dump.py
/usr/local/openvswitch/tools/ovs/ovs-vport-tnl-create-l2.py
/usr/local/openvswitch/tools/ovs/ovs-switch-cleanup.py
/usr/local/openvswitch/tools/ovs/ovs-switch-status.py
/usr/local/openvswitch/tools/vca/vca-switch-status.py
/usr/local/openvswitch/tools/vca/vca-vport-tap-vrf-tnl-create.py
/usr/local/openvswitch/tools/vca/vca-mirror-tests.py
/usr/local/openvswitch/tools/vca/vca-vm-start.sh
/usr/local/openvswitch/tools/vca/dpdk-reinstall-bin-cfg-static
/usr/local/openvswitch/tools/vca/dpdk-reinstall-bin-cfg-dhcp
/usr/local/openvswitch/tools/vca/dpdk-reprogram-ovs-flows
/usr/local/openvswitch/tools/vca/check-port-tp
/usr/local/openvswitch/tools/vca/iperf-run
/usr/local/openvswitch/tools/regress/run_regress.py
/usr/local/openvswitch/tools/system/reinstall-packages
/usr/local/openvswitch/tools/system/update-ovs-vswitchd
/usr/local/openvswitch/tools/system/scattach

/usr/local/openvswitch/third-party/bin/iperf

%pre

%post

%preun
rm -rf /usr/local/openvswitch
exit 0

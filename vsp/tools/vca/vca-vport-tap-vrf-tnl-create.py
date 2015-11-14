#!/usr/bin/python

import sys
import os
import getopt
import time

home = os.environ['HOME'] 
sys.path.append(home + "/bin/testbin/pylib")
sys.path.append(home + "/bin/testbin/pylib/ovs")
sys.path.append(home + "/bin/testbin/pylib/vca")

# generic utility classes
import logger
import net

# generic openvswitch classes
import ovs_helper
import ovs_bridge
import ovs_vport_tap

# VCA specific classes
import vca_helper
import vca_evpn
import vca_vm

def usage():
	print "usage: " + progname + " [-s <ovs-sb>] -i <mgmt-iface> -t <port-type> -l <local-vm-ip> -r <remote-vm-ip> -m <remote-vm-mac> -T <tnl-type>:<rtep-ip> -F [-V <vm-type>]"
	print ""
	print "options:"
	print "-s: name of sandbox to be used for OVS binaries"
	print "-i: management interface to be used"
	print "-t: type of port ('internal' or 'vlan')"
	print "-V: type of VM ('bridge' or 'host' or 'vm' (default))"
	print "-l: local IP address of VM"
	print "-r: IP address of remote OVS switch"
	print "-T: tunnel type of overlay network to be used"
	print "-m: mac address of VM on remote OVS switch"
	print "-F: add default flows for the EVPN"
	sys.exit(1)

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	vm_uuid, vm_xml, vrf_id, evpn_id = vca_helper.set_vrf_defaults(home)
	try:
		opts, args = getopt.getopt(argv, "Chs:i:t:T:l:r:m:FV:");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()

	vm_ip_local = ""
	vm_ip_remote = ""
	vm_mac_remote = ""
	port_type = ""
	mgmt_iface = ""
	tnl_type = ""
	rtep_ip = ""
	add_flows = False
	vm_type = "vm"
	for opt, arg in opts:
		if opt == "-s":
			ovs_sb = arg
			OVS_DIR = home + "/Linux/src/sandbox/" + ovs_sb + "/VCA"
			ovs_path = OVS_DIR + "/utilities"
		elif opt == "-i":
			mgmt_iface = arg
		elif opt == "-t":
			port_type = arg
		elif opt == "-l":
			vm_ip_local = arg
		elif opt == "-V":
			vm_type = arg
		elif opt == "-T":
			Topt_tok = arg.split(":")
			tnl_type = Topt_tok[0]
			rtep_ip = Topt_tok[1]
			tnl_key = ovs_helper.set_tnl_key(tnl_type)
			vrf_tnl_key = str(int(tnl_key))
			evpn_tnl_key = str(int(tnl_key) + 1)
		elif opt == "-r":
			vm_ip_remote = arg
		elif opt == "-m":
			vm_mac_remote = arg
		elif opt == "-F" :
			add_flows = True
		elif opt == "-h":
			usage()

	logfd = logger.open_log(logfile)
	bridge = ovs_bridge.Bridge(ovs_path, br, logfd)
	mgmt_ip = net.get_iface_ip(mgmt_iface)
	vm_iface = ovs_helper.set_vm_iface(mgmt_iface, port_type)

	if (len(vm_ip_local) == 0):
		print(progname + ": Need value of local VM IP address")
		usage()
	if (len(vm_ip_remote) == 0):
		print(progname + ": Need value of remote VM IP address")
		usage()
	if (len(vm_mac_remote) == 0):
		print(progname + ": Need value of remote VM mac address")
		usage()
	if (len(rtep_ip) == 0):
		print(progname + ": Need value of RTEP IP address")
		usage()
	if (len(port_type) == 0):
		print(progname + ": Need value of port type")
		usage()
	if (len(tnl_type) == 0):
		print(progname + ": Need value of tunnel type")
		usage()
	if ((len(vrf_tnl_key) == 0) and (len(evpn_tnl_key) == 0)):
		print(progname + ": Tunnel key not set, specify tunnel type")
		usage()
	if (len(mgmt_iface) == 0):
		print(progname + ": Need value of management interface")
		usage()
	if (port_type != "internal" and port_type != "vlan"):
		print(progname + ": Need a supported type of port")
		exit(1)

	ovs_helper.print_defaults(ovs_path, os_release, hostname, logfile)
	time.sleep(2)

	tap = ovs_vport_tap.Tap(ovs_path, port_type, br, vm_iface,
				vm_ip_local, logfd)
	vm_netmask = tap.get_netmask()
	vm_subnet = tap.get_subnet()
	vm_mac = tap.get_mac()
	vm_gw_ip = tap.get_gw_ip()
	ofp_port_no = tap.get_ofp_port()
	time.sleep(2)

	vm = vca_vm.VM(ovs_path, br, vm_uuid, vm_iface, vm_ip_local, vm_subnet,
		       vm_netmask, vm_gw_ip, vm_mac, vm_xml, vm_type, logfd)
	vm.define()
	time.sleep(2)
	vm.start()
	time.sleep(2)

	evpn = vca_evpn.EVPN(ovs_path, br, logfd, vrf_id, tnl_type,
		             vrf_tnl_key, evpn_id, evpn_tnl_key, mgmt_ip,
			     vm_ip_local)
	time.sleep(2)
	if (add_flows == True):
		evpn.set_flows(vm_iface, vm_ip_local, vm_netmask,
			       vm_subnet, vm_mac, vm_gw_ip, vm_uuid, rtep_ip,
			       vm_ip_remote, vm_mac_remote, vm_type)

	vm_port_no = vm.vm_port()
	port_str = "VM port: " + str(vm_port_no) + ", OFP port: " + str(ofp_port_no)
	if (vm_port_no > 0 and ofp_port_no > 0 and vm_port_no == ofp_port_no):
		print("VM " + vm_uuid + " is resolved, " + port_str)
	else:
		print("VM " + vm_uuid + " is NOT resolved, " + port_str)
		exit(1)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])

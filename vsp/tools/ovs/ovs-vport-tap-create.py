#!/usr/bin/python

import sys
import os
import getopt

home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/vca")
sys.path.append("/usr/local/openvswitch/pylib/dpdk")

# generic utility classes
import logger

# generic openvswitch classes
import ovs_helper
import ovs_bridge
import ovs_vport_tap
import ovs_dpdk_vendor_switch

def usage():
	print "usage: " + progname + " [-s <ovs-sb>] -t <vport-type> -l <local-vm-ip> [-n <val>]"
	print "       " + progname + " [-s <ovs-sb>] -t <vport-type> -l <local-vm-ip> -d -v <DPDK_vendor_name> [-n <val>]"
	print ""
	print "options:"
	print "-i: VM interface to be created"
	print "-t: type of virtual port (internal|vlan)"
	print "-n: number of virtual ports"
	print "-l: local IP address of VM"
	print "-v: OVS DPDK vendor, to be used with -d option (nicira|01.org)"
	print "-d: CSV of pcibus:dev:slot of DPDK devices"
	sys.exit(1)

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	try:
		opts, args = getopt.getopt(argv, "hs:t:l:i:n:v:d:");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	vm_iface = ""
	vm_ip_local = ""
	vport_type = ""
	n_vports = 0
	dpdk_vendor_name = ""
	dpdk_device_list = ""
	ovs_sb = ""
	for opt, arg in opts:
		if opt == "-s":
			ovs_sb = arg
			OVS_DIR = home + "/Linux/src/sandbox/" + ovs_sb + "/VCA"
			ovs_path = OVS_DIR + "/utilities"
			ovs_vswitchd_path = OVS_DIR + "/vswitchd"
		elif opt == "-t":
			vport_type = arg
		elif opt == "-l":
			vm_ip_local = arg
		elif opt == "-i":
			vm_iface = arg
		elif opt == "-n":
			n_vports = arg
		elif opt == "-v":
			dpdk_vendor_name = arg
		elif opt == "-d":
			dpdk_device_list = arg
		else:
			usage()
	if (len(ovs_sb) == 0):
		ovs_vswitchd_path = ovs_path
	if (len(vm_iface) == 0):
		print(progname + ": Need value of VM interface name")
		usage()
	if (len(vm_ip_local) == 0):
		print(progname + ": Need value of local VM IP address")
		usage()
	if (len(vport_type) == 0):
		print(progname + ": Need value of port type")
		usage()
	if ((len(dpdk_device_list) != 0) and (len(dpdk_vendor_name) == 0)):
		print(progname + ": device list requires a valid DPDK vendor")
		usage()
	if ((len(dpdk_vendor_name) != 0) and (len(dpdk_device_list) == 0)):
		print(progname + ": DPDK vendor requires DPDK device list specification")
		usage()
	ovs_helper.print_defaults(ovs_path, os_release, hostname, logfile)
	logfd = logger.open_log(logfile)
	bridge = ovs_bridge.Bridge(ovs_path, br, logfd)
	if ((len(dpdk_vendor_name) != 0) and (len(dpdk_device_list) != 0)):
		ovs_dpdk_switch = ovs_dpdk_vendor_switch.SDK_OVS_Switch()
		ovs_dpdk_obj = ovs_dpdk_switch.alloc_SDK_OVS(dpdk_vendor_name,
							     ovs_vswitchd_path,
							     br,
							     dpdk_device_list)
		print ovs_dpdk_obj.get_vswitchd_cmdline()
		sys.exit(0)
	tap = ovs_vport_tap.Tap(ovs_path, vport_type, br, vm_iface,
				vm_ip_local, logfd)
	vm_mac = tap.get_mac()
	print "VM port mac address: " + vm_mac
	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])


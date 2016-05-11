#!/usr/bin/python

import sys
import os
import getopt
import time

home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/vca")

# generic utility classes
import logger
import net

# generic openvswitch classes
import ovs_helper
import ovs_bridge
import ovs_vport_tap
import ovs_vport_tnl

# VCA specific classes
import vca_flows
import vca_vm

def usage():
	print "usage: " + progname + " [-s <ovs-sb>] -i <mgmt-iface> -t <port-type> -l <local-vm-ip> -r <remote-vm-ip> -T <tnl-type>:<rtep-ip>"
	print ""
	print "options:"
	print "-s: name of sandbox to be used for OVS binaries"
	print "-i: management interface to be used"
	print "-t: type of port ('internal' or 'vlan')"
	print "-l: local IP address of VM"
	print "-r: IP address of remote OVS switch"
	print "-T: tunnel type of overlay network to be used"
	sys.exit(1)

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	try:
		opts, args = getopt.getopt(argv, "hs:i:t:T:l:r:");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()

	vm_ip_local = ""
	port_type = ""
	mgmt_iface = ""
	tnl_type = ""
	rtep_ip = ""
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
		elif opt == "-T":
			Topt_tok = arg.split(":")
			tnl_type = Topt_tok[0]
			rtep_ip = Topt_tok[1]
			tnl_key = ovs_helper.set_tnl_key(tnl_type)
		elif opt == "-r":
			vm_ip_remote = arg
		elif opt == "-h":
			usage()

	logfd = logger.open_log(logfile)
	bridge = ovs_bridge.Bridge(ovs_path, br, logfd)
	mgmt_ip = net.get_iface_ip(mgmt_iface)
	vm_iface = ovs_helper.set_vm_iface(mgmt_iface, port_type)

	if (len(vm_ip_local) == 0):
		print(progname + ": Need value of local VM IP address")
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
	if (len(tnl_key) == 0):
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
	time.sleep(2)

	rtep = ovs_vport_tnl.Tunnel(ovs_path, br, tnl_type, tnl_key, rtep_ip,
				    "rtep", logfd, True)
	rtep_port = rtep.get_tnl_name()
	time.sleep(2)
	ltep = ovs_vport_tnl.Tunnel(ovs_path, br, tnl_type, tnl_key, mgmt_ip,
				    "ltep", logfd, True)
	ltep_port = ltep.get_tnl_name()
	time.sleep(2)

	flow = vca_flows.Flows(ovs_path, br, logfd)
	flow.set_l2_flow(vm_iface, rtep_port)
	flow.set_l2_flow(ltep_port, vm_iface)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])

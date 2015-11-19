#!/usr/bin/python

import sys
import os
import getopt
import time

home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/vca")
sys.path.append("/usr/local/openvswitch/pylib/system")

# generic utility classes
import logger
import net
import process
import shell

# generic openvswitch classes
import ovs_helper
import ovs_bridge
import ovs_vport_tnl

def usage():
	print "usage: " + progname + " [-s <ovs-sb>] -i <mgmt-iface> -t <port-type> -l <local-vm-ip> -r <remote-vm-ip> -T <tnl-type>:<rtep-ip> -n <tunnels>"
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
		opts, args = getopt.getopt(argv, "Chs:i:t:T:l:r:n:");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()

	vm_ip_local = ""
	port_type = ""
	mgmt_iface = ""
	tnl_type = ""
	rtep_ip = ""
	n_tunnels = 0
	for opt, arg in opts:
		if opt == "-s":
			ovs_sb = arg
			OVS_DIR = home + "/Linux/src/sandbox/" + ovs_sb + "/VCA"
			ovs_path = OVS_DIR + "/utilities"
		elif opt == "-C":
			cmd = "ovs-vsctl show | grep Port | grep -v alubr0 | grep -v svc | awk '{print $2}' | sed 's/\"//g'"
			port_list = shell.call_prog_as_is(cmd)
			for port in port_list.splitlines():
				cmd = "ovs-vsctl del-port " + port
				print "Running " + cmd
				shell.call_prog_as_is(cmd)
			sys.exit(1)
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
		elif opt == "-n":
			n_tunnels = int(arg)
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

	for x in range(0, n_tunnels):
		key = tnl_key + str(x)
		print "ITERATION: " + str(x) + ", key: " + key
		rtep = ovs_vport_tnl.Tunnel(ovs_path, br, tnl_type,
					    key, rtep_ip, "rtep", logfd)
		rtep_port = rtep.get_tnl_name()
		ltep = ovs_vport_tnl.Tunnel(ovs_path, br, tnl_type,
					    key, mgmt_ip, "ltep", logfd)
		ltep_port = ltep.get_tnl_name()
		print "Created rtep_port " + rtep_port + " ltep_port " + ltep_port + " with tnl_key " + key
		if (x % 2) == 0:
			print "Deleting rtep_port " + rtep_port
			rtep.destroy()
			print "Deleting ltep_port " + ltep_port
			ltep.destroy()
		if (process.proc_exists("ovs-vswitchd") == False or
		    process.n_procs_by_name("ovs-vswitchd") < 2):
			print "ovs-vswitchd not found, exitting"
			sys.exit(1)
		print
		time.sleep(2)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])


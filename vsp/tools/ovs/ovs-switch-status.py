#!/usr/bin/python

import sys
import os
import getopt

home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/vca")

# generic utility classes
import logger

# generic openvswitch classes
import ovs_helper
import ovs_bridge

def usage():
	print "usage: " + progname + " [-s <ovs-sb>]"
	sys.exit(1)

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	try:
		opts, args = getopt.getopt(argv, "hs:")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-s":
			ovs_sb = arg
			OVS_DIR = home + "/Linux/src/sandbox/" + ovs_sb + "/VCA"
			ovs_path = OVS_DIR + "/utilities"
		else:
			usage()
	logfd = logger.open_log(logfile)
	bridge = ovs_bridge.Bridge(ovs_path, br, logfd)
	bridge.show()
	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])

#!/usr/bin/python

import sys, os, getopt
from os.path import basename

home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_flows
import ovs_ofproto

def usage():
	print "usage: " + progname + " -b <port_name>,<port_name> [-a <port_name>,<port_name>]"
	print "       " + progname + " -s <port_name>,<port_name>"
	print "       " + progname + " -m <in_port>,<dst_mac>,<dst_port_name>"
	print "       " + progname + " -l <port>,<dst_mac>,<src_mac><dst_ip>,<src_ip>"
	print "       " + progname + " -d"
	print ""
	print "Options:"
	print "  -s: setup a flow between specified ports for all packet types"
	print "  -b: setup back-to-back flows between specified ports"
	print "  -a: setup back-to-back ARP flows between specified ports"
	print "  -m: setup a destination mac based flow between specified ports"
	print "  -l: setup a loopback flow on a specified port with modified mac and IP addrs"
	print "  -d: delete all flows"
	sys.exit(1)

def main(argc, argv):
	try:
		opts, args = getopt.getopt(argv,"b:a:ds:m:l:hS")
	except getopt.getOptError:
	 	usage()

	for opt, arg in opts:
		if opt == "-S":
			ovs_path = "/usr/bin"
		else:
			ovs_sb = os.environ['ovs_sb']
			OVS_DIR = home + "/Linux/src/sandbox/" + ovs_sb + "/VCA"
			ovs_path = OVS_DIR + "/utilities"

	hostname = os.uname()[1]
	logfile = home + "/Downloads/logs/" + progname + "." + hostname + ".log"
	logfd = logger.open_log(logfile)
	flow = ovs_flows.Flows(ovs_path, logfd)
	ofproto = ovs_ofproto.OFProto(ovs_path)

	bridge = ofproto.get_bridge()

	for opt, arg in opts:
	 	if opt == "-h":
	 		usage()
		elif opt == "-b":
			port_1, port_2 = arg.split(',', 1)
			flow.set_b2b_flows(bridge, port_1, port_2)
		elif opt == "-a":
			port_1, port_2 = arg.split(',', 1)
			flow.set_arp_flows(bridge, port_1, port_2)
		elif opt == "-m":
			port_1, mac_2, port_2 = arg.split(',', 2)
			flow.set_dst_mac_flow(bridge, port_1, mac_2, port_2)
		elif opt == "-s":
			port_1, port_2 = arg.split(',', 1)
			flow.set_flow(bridge, port_1, port_2)
		elif opt == "-l":
			port, dst_mac, src_mac, dst_ip, src_ip = arg.split(',',
				       					   4)
			flow.set_dst_mac_flow(bridge, port, dst_mac, src_mac,
					      dst_ip, src_ip)
		elif opt == "-d":
			flow.reset(bridge)

if __name__ == "__main__":
	argc = len(sys.argv)
	progname = basename(sys.argv[0])
	main(argc, sys.argv[1:])

#!/usr/bin/python

import sys
import os
import getopt

sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/dpdk")

# DPDK library classes
import dpdk_sys

def usage():
	print "usage: " + progname + " -b -s <dpdk-sb> -t <type> -c"
	print "       " + progname + " -i -s <dpdk-sb> -p <n-pages> -d [<device>,]"
	print "       " + progname + " -S -s <dpdk-sb>"
	print "       " + progname + " -C -s <dpdk-sb>"
	print ""
	print "options:"
	print "-b: build DPDK sandbox"
	print "-C: cleans up system's DPDK configuration"
	print "-S: displays status"
	print "-t: type of target - ivshmem or default (used with -b or -c)"
	print "-c: configures before doing a build"
	print "-d: CSV of PCI device(s) in domain:bus:slot.func"
	print "-p: number of hugeTLBfs pages to be configured"
	sys.exit(1)

def main(argc, argv):
	try:
		opts, args = getopt.getopt(argv, "hs:bciCt:p:d:S");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	b_flag = 0
	c_flag = 0
	i_flag = 0
	C_flag = 0
	s_flag = 0
	dpdk_sb = ""
	tgt_config = "default"
	n_pages = ""
	device_list = ""
	for opt, arg in opts:
		if opt == "-b":
			b_flag = 1
		elif opt == "-c":
			c_flag = 1
		elif opt == "-i":
			i_flag = 1
		elif opt == "-t":
			tgt_config = arg
		elif opt == "-C":
			C_flag = 1
		elif opt == "-s":
			dpdk_sb = arg
		elif opt == "-S":
			s_flag = 1
		elif opt == "-p":
			n_pages = arg
		elif opt == "-d":
			device_list = arg
		else:
			usage()
	dpdk = dpdk_sys.DPDK_System(home, progname, dpdk_sb)
	if (b_flag == 1):
		rc = dpdk.build(tgt_config, c_flag)
	elif (C_flag == 1):
		rc = dpdk.cleanup(tgt_config)
	elif (s_flag == 1):
		rc = dpdk.status()
		if (rc == 0):
			rc = dpdk.print_device_list()
	elif (i_flag == 1):
		rc = dpdk.reset(tgt_config, n_pages, device_list)
	if (rc != 0):
		usage()

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])


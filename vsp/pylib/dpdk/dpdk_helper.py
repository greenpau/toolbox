#!/usr/bin/python

import os
import cpu

def set_defaults(home, progname, tgt_config, type):
	hostname = os.uname()[1]
	machine = os.uname()[4]
	logfile = home + "/Downloads/logs/" + progname + "-" + type + "." + hostname + ".log"
	tgt = ""
	if (tgt_config != ""):
		tgt = machine + "-" + tgt_config + "-linuxapp-gcc"
	return logfile, tgt

def print_defaults(tgt, c_flag, dpdk_path, logfile):
	print "DPDK path: " + dpdk_path
	print "Logfile: " + logfile
	if (tgt != ""):
		print "Target: " + tgt
	print "Configure: " + str(c_flag)

def get_dpdk_cpu_coremask():
	nprocs = cpu.get_nprocs()
	if (nprocs == 0):
		coremask = "0x0"		# none
	elif (nprocs == 1):
		coremask = "0x1"		# use the only core (shared)
	elif (nprocs == 2 or nprocs == 3):
		coremask = "0x3"		# use 2 cores
	elif (nprocs == 4):
		coremask = "0x7"		# use 3 cores
	else:
		coremask = "0xf"		# use 4 cores
	return coremask

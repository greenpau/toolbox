#!/usr/bin/python

import os

def set_tnl_key(tnl_type):
	if (tnl_type == "vxlan"):
		tnl_key = str(1234)
	elif (tnl_type == "gre"):
		tnl_key = str(5678)
	elif (tnl_type == "mpls-gre"):
		tnl_key = "9abc"
	else:
		tnl_key = ""
	return tnl_key

def set_vm_iface(mgmt_iface, port_type):
	if (port_type == "vlan"):
		vm_iface = mgmt_iface + "." + vlan_id
	else:
		vm_iface = "vport1"
	return vm_iface

def set_defaults(home, progname):
	ovs_path = "/usr/bin"
	hostname = os.uname()[1]
	os_release = os.uname()[2]
	logfile = home + "/Downloads/logs/" + progname + "." + hostname + ".log"
	br = "alubr0"
	vlan_id = str(1)
	return ovs_path, hostname, os_release, logfile, br, vlan_id

def print_defaults(ovs_path, os_release, hostname, logfile):
	print "Hostname: " + hostname
	print "OS Release: " + os_release
	print "VCA path: " + ovs_path
	print "Log: " + logfile

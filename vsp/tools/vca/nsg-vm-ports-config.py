#!/usr/bin/python

import sys
import os
import getopt
import time

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
import net
import shell
import ns

# OVS classes
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_helper
import ovs_vport_tap
import ovs_vport_tnl
import ovs_flows

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_helper
import vca_evpn
import vca_vm
import vca_json_config

def usage():
	print "usage: " + progname + " -c -u <uplink> -V <vm-type> [-C <json-config-file>]"
	print "       " + progname + " -d [-C <json-config-file>]"
	print "       " + progname + " -s all|vport_name"
	print ""
	print "options:"
	print "-u: uplink interface to be used"
	print "-V: type of vport ('bridge' or 'host' or 'vm' (default))"
	print "-C: configuration file (in json)"
	print "-c: configure NSG vports"
	print "-d: deconfigure NSG vports"
	print "-s: status of NSG vport(s) - 'all' or CSV vm1,vm2"
	sys.exit(1)

def main(argc, argv):
	home = os.environ['HOME']
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	vm_uuid, vm_xml, vrf_id, evpn_id = vca_helper.set_vrf_defaults(home)
	logfd = logger.open_log(logfile)
	ovs_helper.print_defaults(ovs_path, os_release, hostname, logfile)

	try:
		opts, args = getopt.getopt(argv, "hu:C:V:cds:");
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()

	config_file = "/usr/local/openvswitch/templates/vm_ports_default_config.json"
	uplink_iface = "port1"
	configure = False
	deconfigure = False
	status = False
	status_arg = ""
	rc = 0
	for opt, arg in opts:
		if opt == "-c":
			configure = True
		elif opt == "-d":
			deconfigure = True
		elif opt == "-s":
			status = True
			status_arg = arg
		elif opt == "-u":
			uplink_iface = arg
		elif opt == "-C":
			config_file = arg
		elif opt == "-h":
			usage()

	if (configure == False and deconfigure == False and status == False):
		print progname + ": invalid usage"
		usage

	if (configure == True):
		rc = do_configure(progname, ovs_path, br, config_file,
				  uplink_iface, logfd)
	elif (deconfigure == True):
		rc = do_deconfigure(config_file, logfd)
	elif (status == True):
		rc = do_status(progname, ovs_path, br, config_file,
			       status_arg, logfd)
	sys.exit(rc)

def read_configuration(config_file, logfd):
	vrfs_cfg_obj = vca_json_config.Json_Config_Vrfs(config_file, logfd)
	all_vrfs_cfg = vrfs_cfg_obj.read()
	n_vrfs = vrfs_cfg_obj.count()

	evpns_cfg_obj = vca_json_config.Json_Config_Evpns(config_file, logfd)
	all_evpns_cfg = evpns_cfg_obj.read()
	n_evpns = evpns_cfg_obj.count()

	vms_cfg_obj = vca_json_config.Json_Config_Vms(config_file, logfd,
						      evpns_cfg_obj,
						      vrfs_cfg_obj)
	all_vms_cfg = vms_cfg_obj.read()
	n_vms = vms_cfg_obj.count()
	return vrfs_cfg_obj, all_vrfs_cfg, n_vrfs, evpns_cfg_obj, all_evpns_cfg, n_evpns, vms_cfg_obj, all_vms_cfg, n_vms

def do_configure(progname, ovs_path, br, config_file, uplink_iface, logfd):
	vm_type = "vm"
	vm_netmask = "24"
	uplink_ip = net.get_iface_ip(uplink_iface)
	if (uplink_ip == None) or (uplink_ip == ""):
		print progname + ": no IP address configured on " + uplink_iface
		sys.exit(1)

	vrfs_cfg_obj, all_vrfs_cfg, n_vrfs, evpns_cfg_obj, all_evpns_cfg, n_evpns, vms_cfg_obj, all_vms_cfg, n_vms = read_configuration(config_file, logfd)

	print
	print "Parameters:"
	print "Config File: " + config_file
	print "Uplink: " + uplink_iface + ", IP: " + uplink_ip
	print "Number of VRFs: " + str(n_vrfs)
	print "Number of EVPNs: " + str(n_evpns)
	print "Number of VMs: " + str(n_vms)
	print

	ingress_rate = 4294967295
	ingress_peak_rate = 4294967295
	ingress_burst = 4294967295
	ingress_bum_rate = 4294967295
	ingress_bum_peak_rate = 4294967295
	ingress_bum_burst = 4294967295
	ingress_fip_rate = 0
	ingress_fip_peak_rate = 0
	ingress_fip_burst = 0
	ingress_fip_rate = 4294967295
	ingress_fip_peak_rate = 4294967295
	ingress_fip_burst = 4294967295
	egress_fip_rate = 0
	egress_fip_peak_rate = 0
	egress_fip_burst = 0
	egress_fip_rate = 6000
	egress_fip_peak_rate = 6000
	egress_fip_burst = 100
	egress_class = 3

	ns_list = ns.namespaces(n_vms, 0)
	ns_list.setup()

	for this_vm_cfg in all_vms_cfg:
		valid, vm_name, vm_iface, vm_uuid, vm_ip, vm_mac, evpn_id, evpn_tnl_key, tnl_type, evpn_subnet, evpn_netmask, evpn_gw_ip, evpn_gw_mac, vrf_id, vrf_tnl_key = vms_cfg_obj.vm_attrs(this_vm_cfg)
		if (valid == False) or (vm_name == ""):
			continue
		print "VM: " + vm_name + ", UUID: " + vm_uuid
		print "\tIP: " + vm_ip + ", MAC: " + vm_mac
		print "\tEVPN: " + evpn_id + ", tnl_type: " + tnl_type + ", tnl_key: " + evpn_tnl_key + ", subnet: " + evpn_subnet + ", mask: " + evpn_netmask + ", gw_ip: " + evpn_gw_ip + ", gw_mac: " + evpn_gw_mac
		print "\tVRF: " + vrf_id + ", vrf_tnl_key: " + vrf_tnl_key
		ns_list.set_mac(vm_name, vm_mac)
		#ns_list.set_ip(vm_name, vm_ip, vm_netmask)
		evpn = vca_evpn.EVPN(ovs_path, br, logfd, vrf_id, tnl_type,
				     vrf_tnl_key, evpn_id, evpn_tnl_key,
				     evpn_subnet, evpn_netmask, evpn_gw_ip,
				     evpn_gw_mac, uplink_ip, None)
		vm = vca_vm.VM(ovs_path, br, vm_name, vm_uuid, vm_iface, vm_ip,
			       evpn_subnet, evpn_netmask, evpn_gw_ip, vm_mac,
			       None, vm_type, logfd)
		vm.add_port()
		vm.add_membership(evpn_id)
		vm.add_acls()
		vm.add_routes(vrf_id, evpn_id)
		vm.add_dhcp()
		vm.enable_mac_learning()
		vm.add_qos(ingress_rate, ingress_peak_rate, ingress_burst,
			   ingress_bum_rate, ingress_bum_peak_rate,
			   ingress_bum_burst,
			   ingress_fip_rate, ingress_fip_peak_rate,
			   ingress_fip_burst,
			   egress_class,
			   egress_fip_rate, egress_fip_peak_rate, egress_fip_burst)
		time.sleep(1)
		ns_list.get_ip(vm_name)
		print
	return 0

def do_deconfigure(config_file, logfd):
	vrfs_cfg_obj, all_vrfs_cfg, n_vrfs, evpns_cfg_obj, all_evpns_cfg, n_evpns, vms_cfg_obj, all_vms_cfg, n_vms = read_configuration(config_file, logfd)

	print
	print "Parameters:"
	print "Config File: " + config_file
	print "Number of VRFs: " + str(n_vrfs)
	print "Number of EVPNs: " + str(n_evpns)
	print "Number of VMs: " + str(n_vms)
	print

	ns_list = ns.namespaces(n_vms, 0)
	ns_list.destroy()

	cmd = [ "service", "openvswitch", "restart" ]
	shell.run_cmd("Restarting openvswitch", cmd, logfd)

	return 0

def do_status(progname, ovs_path, br, config_file, status_arg, logfd):
	vrfs_cfg_obj, all_vrfs_cfg, n_vrfs, evpns_cfg_obj, all_evpns_cfg, n_evpns, vms_cfg_obj, all_vms_cfg, n_vms = read_configuration(config_file, logfd)
	vm_type = "vm"

	print
	print "Parameters:"
	print "Config File: " + config_file
	print "Number of VRFs: " + str(n_vrfs)
	print "Number of EVPNs: " + str(n_evpns)
	print "Number of VMs: " + str(n_vms)
	print

	if (status_arg != ""):
		vm_list = status_arg.split(",")
	else:
		vm_list = [ "all" ]
	ns_list = ns.namespaces(n_vms, 0)
	for this_vm_name in vm_list:
		ns_list.show(this_vm_name)
		found = False
		for this_vm_cfg in all_vms_cfg:
			valid, vm_name, vm_iface, vm_uuid, vm_ip, vm_mac, evpn_id, evpn_tnl_key, tnl_type, evpn_subnet, evpn_netmask, evpn_gw_ip, evpn_gw_mac, vrf_id, vrf_tnl_key = vms_cfg_obj.vm_attrs(this_vm_cfg)
			if (valid == False) or (vm_name == ""):
				continue
			if (this_vm_name == vm_name):
				found = True
				break
		if (found == False):
			continue
		vm = vca_vm.VM(ovs_path, br, vm_name, vm_uuid, vm_iface, vm_ip,
			       evpn_subnet, evpn_netmask, evpn_gw_ip, vm_mac,
			       None, vm_type, logfd)
		vm.show()
		vm.dump_flows()

	return 0

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])

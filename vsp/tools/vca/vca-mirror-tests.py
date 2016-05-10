#!/usr/bin/python

import sys
import os
import getopt

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
import net
import shell

# OVS classes
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_helper
import ovs_vport_tap
import ovs_vport_tnl

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_test
import vca_pbm
import vca_vpm
import vca_dyn
import vca_vm

def usage():
	print "usage: " + progname + " [options]"
	print "options:"
	print "    -v vm_name(s): comma separated VM names for mirroring"
	print "    -r <ip>: remote ovs IPv4 address"
	print "    -i <ip>: mirror destination IPv4 address"
	print "    -p <name>: mirror destination port (dyn-mirror)"
	print "    -e: exitOnFailure=true"
	print "    -s <suite>: CSV of suite name(s) to run ('PBM', 'VPM', 'DYN')"
	sys.exit(1)

############################### HELPERS #####################################
def get_vm_attr__(ovs_path, br, logfd, vm_name):
	vm = vca_vm.VM(ovs_path, br, None, None, None, None, None, None,
		       None, None, None, logfd)
	vm.set_vm_name(vm_name)
	port_name = vm.port_name()
	mac = vm.port_mac()
	ip = vm.port_ip()
	ofp_port = vm.port_ofp_port()
	vrf_id = vm.vrf_id()
	return port_name, mac, ip, ofp_port, vrf_id

def get_tunnel_attr__(ovs_path, br, logfd, remote_ovs_ip):
	tnl = ovs_vport_tnl.Tunnel(ovs_path, br, None, None, remote_ovs_ip,
				    "rtep", logfd)
	mac = "00:11:22:33:44:55"
	ip = "1.2.3.4"
	ofp_port = tnl.get_ofp_port()
	tunnel_port = tnl.get_tnl_name()
	return tunnel_port, mac, ip, ofp_port

def mirror_verify_destination__(param):
	mobj = param['mirror_obj']
	in_mirror_dst = param['mirror_dst']
	mobj_destination = str(mobj.get_destination())
	if (in_mirror_dst != mobj_destination):
		print "Mirror Destination IP verification failed (expected: " + in_mirror_dst + ", got: " + mobj_destination + ")"
		return False
	else :
		print "Mirror Destination IP verification passed"
	return True

def mirror_verify_internal_name__(param):
	mobj = param['mirror_obj']
	mirror_dst_ip = param['mirror_dst_ip']
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	mobj_internal_name = str(mobj.get_internal_name())
	if (mirror_tunnel != mobj_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + mobj_internal_name + ")"
		return False
	else :
		print "Mirror Internal Name verification passed"
	return True

def mirror_verify_tunnel_ofp_port__(param):
	mobj = param['mirror_obj']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mobj_iface, mobj_ports = mobj.get_tunnel_port()
	mobj_tap = ovs_vport_tap.Tap(ovs_path, "gre", br, mobj_iface,
				     "0.0.0.0", logfd)
	ovs_ofp_port = str(mobj_tap.get_ofp_port())
	mobj_ofp_port = mobj_ports.split("/")[0]
	if (ovs_ofp_port != mobj_ofp_port):
		print "Mirror Tunnel Port verification failed (expected: " + ovs_ofp_port + ", got: " + mobj_ofp_port + ")"
		return False
	else :
		print "Mirror Tunnel Port verification passed"
	return True

def mirror_verify_nrefs__(param):
	mobj = param['mirror_obj']
	mirror_nrefs = param['mirror_nrefs']
	mobj_nrefs = str(mobj.get_nrefs())
	if (mirror_nrefs != mobj_nrefs):
		print "Mirror Num Refs verification failed (expected: " + mirror_nrefs + ", got: " + mobj_nrefs + ")"
		return False
	else :
		print "Mirror Num Refs verification passed"
	return True

def mirror_verify_all__(mobjs, param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	pbm_dir = param['pbm_dir']
	vpm_dir = param['vpm_dir']
	acl_type = param['acl_type']
	nrefs = param['nrefs']
	passed = True
	n_sub_tests = 0

	for mobj in mobjs:
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst' : mirror_dst_ip,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_destination__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst_ip' : mirror_dst_ip,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_internal_name__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'ovs_path' : ovs_path,
				'br' : br,
				'logfd' : logfd,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_tunnel_ofp_port__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'mirror_nrefs' : nrefs,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_nrefs__(st_param)
		if (passed == False):
			break
	return passed, n_sub_tests

def mirror_verify_cleanup__(param):
	mobj = param['mirror_obj']
	ovs_path = param['ovs_path']
	mirror_dst_ip = param['mirror_dst_ip']
	n_sub_tests = 0

	mobj_destination = mobj.get_destination()
	n_sub_tests = n_sub_tests + 1
	if (mobj_destination != None):
		print "mirror cleanup check failed"
		return False, n_sub_tests
	else:
		print "mirror cleanup check passed"

	mirror_tunnel = "t" + net.ipaddr2hex(mirror_dst_ip)
	cmd = [ ovs_path + "/ovs-appctl", "dpif/show" ]
	dpif_show_out = shell.execute(cmd).splitlines()
	n_sub_tests = n_sub_tests + 1
	for line in dpif_show_out:
		if (line.find(mirror_tunnel) >= 0):
			print "mirror tunnel not cleaned up"
			return False, n_sub_tests
	print "mirror tunnel cleanup check passed"
	return True, n_sub_tests


################################# PBM ########################################
def pbm_verify_flow_attrs__(param):
	pbm = param['mirror_obj']
	mirror_dir = param['mirror_dir']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	acl_type = param['acl_type']
	acl_type_verified = False
	mirror_attrs = pbm.get_mirror_flow_attrs()
	for mirror_attr in mirror_attrs:
		table_id = mirror_attr['table_id']
		if (table_id == "9"):
			flow_acl_type = "Ingress"
		elif (table_id == "14"):
			flow_acl_type = "Egress"
		elif (table_id == "10"):
			flow_acl_type = "Redirect"
		else:
			print "Flow returned bad table_id: " + table_id
			return False
		flow_mirror_id = mirror_attr['mirror_id']
		flow_mirror_dst_ip = mirror_attr['mirror_dst_ip']
		if (table_id == "10") and (flow_acl_type == acl_type):
			acl_type_verified = True
			print "Flow Mirror ACL Type verification passed"
		else:
			if (flow_acl_type != mirror_dir):
				continue
			else:
				acl_type_verified = True
				print "Flow Mirror ACL Type verification passed"
		if (flow_mirror_id != mirror_id):
			print "Flow Mirror ID verification failed (expected: " + mirror_id + ", got: " + flow_mirror_id + ")"
			return False
		else:
			print "Flow Mirror ID verification passed"
		if (flow_mirror_dst_ip != mirror_dst_ip):
			print "Flow Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + flow_mirror_dst_ip + ")"
			return False
		else:
			print "Flow Mirror Destination IP verification passed"
	if (acl_type_verified == False):
		print "Flow Mirror ACL type verification failed (expected: " + mirror_dir + ", but not found in dump-detailed-flows, " + flow_acl_type + ")"
		return False
	return True

def pbm_verify_mirror_vport__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	vm_name = param['vm_name']
	pbm = param['mirror_obj']
	mirror_dir = param['mirror_dir']
	acl_type = param['acl_type']

	if (acl_type != "Redirect"):
		acl_type = mirror_dir
	mirror_vport, mirror_vport_ofp_port, mirror_vport_odp_port = pbm.get_mirror_vport(acl_type)
	port_name, dst_mac, dst_ip, dst_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, vm_name)
	if (port_name == mirror_vport):
		print "Mirror VPORT name verification passed (" + mirror_vport_ofp_port + "/" + mirror_vport_odp_port + ")" 
	else:
		print "Mirror vport: " + mirror_vport + ", mirror_ofp_port: " + mirror_vport_ofp_port + ", vport: " + vport
		print "mirror VPORT name verification failed"
		return False
	return True

def pbm_single_mirror__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	acl_dir = param['pbm_dir']
	acl_type = param['acl_type']
	custom_action = param['custom_action']
	n_sub_tests = 0

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	if (custom_action != None):
		pbm.set_custom_action(custom_action)
	pbm.local_create(acl_type, acl_dir)
	pbm.dump(False)
	pbm.show(False)
	mobjs = [ pbm ]
	param['nrefs'] = "1"
	passed, n_this_sub_tests = mirror_verify_all__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests
	st_param = {	'mirror_obj' : pbm,
			'mirror_dir' : acl_dir,
			'acl_type' : acl_type,
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests
	st_param = {	'ovs_path' : ovs_path,
			'br' : br,
			'logfd': logfd,
			'vm_name': vm_name,
			'mirror_obj' : pbm,
			'acl_type' : acl_type,
			'mirror_dir' : acl_dir,
	}
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_mirror_vport__(st_param)
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests
	pbm.local_destroy()
	st_param = {	'mirror_obj' : pbm,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def pbm_multiple_acl_mirrors__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	acl_type = param['acl_type']
	n_sub_tests = 0

	if (acl_type == "Redirect"):
		print "Multiple ACL mirror tests skipped for redirect ACL"
		return True, n_sub_tests
	pbm1 = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			   vm_name)
	pbm1.local_create(acl_type, "Ingress")
	pbm1.dump(False)
	pbm1.show(False)
	pbm2 = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			   vm_name)
	pbm2.local_create(acl_type, "Egress")
	pbm2.dump(False)
	pbm2.show(False)
	mobjs = [ pbm1, pbm2 ]
	param['nrefs'] = "2"
	passed, n_this_sub_tests = mirror_verify_all__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		pbm1.local_destroy()
		pbm2.local_destroy()
		return False, n_sub_tests
	st_param = {	'mirror_obj' : pbm1,
			'mirror_dir' : "Ingress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
			'acl_type' : acl_type,
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
	st_param = {	'mirror_obj' : pbm2,
			'mirror_dir' : "Egress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
			'acl_type' : acl_type,
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
	pbm1.local_destroy()
	pbm2.local_destroy()
	st_param = {	'mirror_obj' : pbm1,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	st_param = {	'mirror_obj' : pbm2,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def pbm_single_mirror(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	acl_dirs = [ "Ingress", "Egress" ]
	global testcase_id

	for acl_dir in acl_dirs:
		param = { 'ovs_path' : ovs_path,
			  'br' : br,
			  'logfd' : logfd,
		          'mirror_id': "9900",
			  'mirror_dst_ip': mirror_dst_ip,
			  'vm_name': vm_name,
			  'pbm_dir' : acl_dir,
			  'vpm_dir' : None,
			  'acl_type' : acl_type,
			  'custom_action': None,
			}
		testcase_desc = "Single ACL Mirror: " + acl_dir + " " + acl_type
		test = vca_test.TEST(testcase_id, testcase_desc,
				     pbm_single_mirror__, param)
		suite.register_test(test)
		test.run()
		suite.assert_test_result(test)
		testcase_id = testcase_id + 1
	return

def pbm_multiple_acl_mirrors(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	global testcase_id
	param = { 'ovs_path' : ovs_path,
		  'br' : br,
		  'logfd' : logfd,
	          'mirror_id': "9900",
		  'mirror_dst_ip': mirror_dst_ip,
		  'vm_name': vm_name,
		  'pbm_dir' : None,
		  'vpm_dir' : None,
		  'acl_type' : acl_type,
		}
	testcase_desc = "Multiple ACL Mirror: " + acl_type
	test = vca_test.TEST(testcase_id, testcase_desc,
			     pbm_multiple_acl_mirrors__, param)
	suite.register_test(test)
	test.run()
	suite.assert_test_result(test)
	testcase_id = testcase_id + 1
	return

def pbm_vpm_single_mirror__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	pbm_dir = param['pbm_dir']
	vpm_dir = param['vpm_dir']
	acl_type = param['acl_type']
	n_sub_tests = 0

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	pbm.local_create(acl_type, pbm_dir)
	pbm.dump(False)
	pbm.show(False)

	vpm = vca_vpm.VPM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	vpm.local_create(vpm_dir)
	vpm.dump(False)
	vpm.show(False)

	mobjs = [ pbm, vpm ]
	param['nrefs'] = "1"
	passed, n_this_sub_tests = mirror_verify_all__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		vpm.local_destroy()
		pbm.local_destroy()
		return False, n_sub_tests
	st_param = {	'mirror_obj' : pbm,
			'mirror_dir' : pbm_dir,
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
			'acl_type' : acl_type,
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
	if (passed == False):
		pbm.local_destroy()
		vpm.local_destroy()
		return False, n_sub_tests
	st_param = {	'ovs_path' : ovs_path,
			'br' : br,
			'logfd': logfd,
			'vm_name': vm_name,
			'mirror_obj' : pbm,
			'mirror_dir' : pbm_dir,
			'acl_type' : acl_type,
	}
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_mirror_vport__(st_param)
	if (passed == False):
		pbm.local_destroy()
		vpm.local_destroy()
		return False, n_sub_tests
	pbm.local_destroy()
	vpm.local_destroy()
	st_param = {	'mirror_obj' : pbm,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	st_param = {	'mirror_obj' : vpm,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def pbm_vpm_single_mirror(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	global testcase_id
	acl_dirs = [ "Ingress", "Egress" ]
	vpm_dirs = [ "Ingress", "Egress", "both" ]

	for pbm_dir in acl_dirs:
		for vpm_dir in vpm_dirs:
			param = { 'ovs_path' : ovs_path,
				  'br' : br,
				  'logfd' : logfd,
			          'mirror_id': "9900",
				  'mirror_dst_ip': mirror_dst_ip,
				  'vm_name': vm_name,
				  'pbm_dir' : pbm_dir,
				  'vpm_dir' : vpm_dir,
				  'acl_type' : acl_type,
				}
			testcase_desc = "PBM/VPM Single ACL Mirror: PBM - " + pbm_dir + " " + acl_type + ", VPM - " + vpm_dir
			test = vca_test.TEST(testcase_id, testcase_desc,
					     pbm_vpm_single_mirror__, param)
			suite.register_test(test)
			test.run()
			suite.assert_test_result(test)
			testcase_id = testcase_id + 1
	return

def pbm_traffic_ofproto_trace__(param):
	passed = True
	pbm = param['pbm']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	acl_type = param['acl_type']
	otdtf = param['otdtf']

	pkt = "in_port=" + dst_ofp_port + ",dl_src=" + src_mac + ",dl_dst=" + dst_mac + ",dl_type=0x0800,nw_src=" + src_ip + ",nw_dst=" + dst_ip + ",nw_proto=17,nw_tos=0xff,nw_ttl=128"
	cmd = [ ovs_path + "/ovs-appctl", "ofproto/trace", br, pkt ]
	out = shell.execute(cmd).splitlines()
	for l in out:
		if (l.find("Datapath actions:") < 0):
			continue
		if (l.find("tunnel") < 0):
			outstr = "Datapath actions donot contain mirror tunnel info"
			if (acl_type == "reflexive"):
				outstr = outstr + ", passed"
			else:
				outstr = outstr + ", failed"
				passed = False
			print outstr
			return passed
		if (otdtf < len(l.split(","))):
			tep_odp_port = l.split(",")[otdtf]
		else:
			tep_odp_port = None
		mobj_iface, mobj_ports = pbm.get_tunnel_port()
		if (mobj_ports != None):
			mobj_odp_port = mobj_ports.split("/")[1]
		else:
			mobj_odp_port = None
		if (tep_odp_port == None or mobj_odp_port == None):
			passed = False
			print "failed to parse TEP odp port or mirror object odp port: " + l
			return passed
		elif (tep_odp_port != mobj_odp_port):
			passed = False
			print "TEP odp port (ofproto/trace): " + tep_odp_port + ", mirror object odp port: " + mobj_odp_port + ", failed, " + l
			return passed
		print "ofproto/trace of packet detected packet sent to mirror tunnel, passed"
		return passed
	return passed

def pbm_traffic_pkt_out__(param):
	passed = True
	n_sub_tests = 0
	pbm = param['pbm']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	src_ofp_port = param['src_ofp_port']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	acl_type = param['acl_type']
	pbm_dir = param['pbm_dir']
	mirror_id = param['mirror_id']
	n_pkts_sent = int(10)

	cmd = [ ovs_path + "/ovs-appctl", "bridge/clear-flow-stats", br ]
	shell.execute(cmd)

	if (acl_type == "reflexive"):
		if (pbm_dir == "Egress"):
			mac_1 = src_mac
			ip_1 = src_ip
			mac_2 = dst_mac
			ip_2 = dst_ip
			ofp_port = src_ofp_port
		else:
			mac_1 = dst_mac
			ip_1 = dst_ip
			mac_2 = src_mac
			ip_2 = src_ip
			ofp_port = dst_ofp_port
	else:
		mac_1 = src_mac
		ip_1 = src_ip
		mac_2 = dst_mac
		ip_2 = dst_ip
		ofp_port = dst_ofp_port

	mirror_iface, mirror_ports = pbm.get_tunnel_port()
	if (mirror_iface == None):
		passed = False
		print "Failed to parse mirror interface"
		return passed, n_sub_tests
	tap = ovs_vport_tap.Tap(ovs_path, None, br, mirror_iface,
				"0.0.0.0", logfd)
	curr_n_pkts, curr_n_bytes = tap.get_pkt_stats()

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")

	if (acl_type == "Redirect") :
		rule_n_packets, rule_n_bytes, flow = pbm.get_flow_pkt_counters(acl_type)
		flow_n_packets, flow_n_bytes, flow = pbm.get_flow_pkt_counters_mirror(acl_type)
	else:
		rule_n_packets, rule_n_bytes, flow = pbm.get_flow_pkt_counters(pbm_dir)
		flow_n_packets, flow_n_bytes, flow = pbm.get_flow_pkt_counters_mirror(pbm_dir)
	n_sub_tests = n_sub_tests + 1
	if (rule_n_packets == 0):
		passed = False
		print "Packet count is 0 in rule: " + flow
		return passed, n_sub_tests
	if (acl_type == "Redirect"):
		print "Rule packet count is non-zero in " + acl_type + " ACL, passed" 
	else:
		print "Rule packet count is non-zero in " + pbm_dir + " ACL, passed" 

	if (flow_n_packets == 0):
		passed = False
		print "Mirror Packet count is 0 in rule: " + flow
		return passed, n_sub_tests
	if (acl_type == "Redirect"):
		print "Rule mirror packet count is non-zero in " + acl_type + " ACL, passed" 
	else:
		print "Rule mirror packet count is non-zero in " + pbm_dir + " ACL, passed" 

	n_sub_tests = n_sub_tests + 1
	if (flow_n_packets == -1) or (flow_n_bytes == -1):
		passed = False
		print "Mirror attribute NOT found in rule: " + flow
		return passed, n_sub_tests
	if (acl_type == "Redirect"):
		print "Mirror attribute found for rule in " + acl_type + " ACL, passed" 
	else:
		print "Mirror attribute found for rule in " + pbm_dir + " ACL, passed" 

	n_sub_tests = n_sub_tests + 1
	if (flow_n_packets != rule_n_packets):
		passed = False
		print "bridge/dump-flows-detail: flow_n_packets: " + str(flow_n_packets) +  ", rule_n_packets: " + str(rule_n_packets) + ", mismatch, failed"
		print flow
		return passed, n_sub_tests
	print "bridge/dump-flows-detail: flow_n_packets (" + str(flow_n_packets) + ") = rule_n_packets (" + str(rule_n_packets) + "), passed"

	n_sub_tests = n_sub_tests + 1
	if (flow_n_bytes != rule_n_bytes):
		passed = False
		print "bridge/dump-flows-detail: flow_n_bytes: " + str(flow_n_bytes) +  ", rule_n_bytes: " + str(rule_n_bytes) + ", mismatch, failed"
		print flow
		return passed, n_sub_tests
	print "bridge/dump-flows-detail: flow_n_bytes (" + str(flow_n_bytes) + ") = rule_n_bytes (" + str(rule_n_bytes) + "), passed"

	mirror_n_packets, mirror_n_bytes = pbm.get_mirror_traffic_stats()

	n_sub_tests = n_sub_tests + 1
	if (mirror_n_packets != flow_n_packets):
		passed = False
		print "mirror-show/n_packets: " + mirror_n_packets + ", flow_n_packets: " + flow_n_packets + ", mismatch, failed"
		return passed, n_sub_tests
	print "mirror-show/n_packets (" + mirror_n_packets + ") = bridge/dump-flows-detail (" + flow_n_packets + "), passed"

	n_sub_tests = n_sub_tests + 1
	if (mirror_n_bytes != flow_n_bytes):
		passed = False
		print "mirror-show/n_bytes: " + mirror_n_bytes + ", flow_n_bytes: " + flow_n_bytes + ", mismatch, failed"
		return passed, n_sub_tests
	print "mirror-show/n_bytes (" + mirror_n_bytes + ") = bridge/dump-flows-detail (" + flow_n_bytes + "), passed"

	mirror_attrs = pbm.get_mirror_flow_attrs()
	for mirror_attr in mirror_attrs:
		flow_mirror_id = mirror_attr['mirror_id']
		if (flow_mirror_id != mirror_id):
			continue

		mirror_attr_table_id = mirror_attr['table_id']
		n_sub_tests = n_sub_tests + 1
		if (acl_type == "Redirect") and (mirror_attr_table_id == "10"):
			print "bridge/dump-flows-detail: redirect mirror table_id check passed"
		elif (pbm_dir == "Ingress") and (mirror_attr_table_id == "9"):
			print "bridge/dump-flows-detail: ingress mirror table_id check passed"
		elif (pbm_dir == "Egress") and (mirror_attr_table_id == "14"):
			print "bridge/dump-flows-detail: egress mirror table_id check passed"
		elif (acl_type == "Redirect"):
			print "bridge/dump-flows-detail: table_id: " + mirror_attr_table_id + ", acl_type: " + acl_type + ", failed"
		else:
			print "bridge/dump-flows-detail: table_id: " + mirror_attr_table_id + ", pbm_dir: " + pbm_dir + ", failed"
			passed = False
			return passed, n_sub_tests

		mirror_attr_n_packets = mirror_attr['mirror_n_packets']
		n_sub_tests = n_sub_tests + 1
		if (flow_n_packets != mirror_attr_n_packets):
			passed = False
			print "bridge/show-mirror: flow_n_packets: " + str(flow_n_packets) +  ", mirror_attr_n_packets: " + str(mirror_attr_n_packets) + ", mismatch, failed"
			return passed, n_sub_tests
		print "bridge/show-mirror: flow_n_packets (" + str(flow_n_packets) + ") = mirror_attr_n_packets (" + str(mirror_attr_n_packets) + "), passed"

		mirror_attr_n_bytes = mirror_attr['mirror_n_bytes']
		n_sub_tests = n_sub_tests + 1
		if (flow_n_bytes != mirror_attr_n_bytes):
			passed = False
			print "bridge/show-mirror: flow_n_packets: " + str(flow_n_packets) +  ", mirror_attr_n_bytes: " + str(mirror_attr_n_bytes) + ", mismatch, failed"
			return passed, n_sub_tests
		print "bridge/show-mirror: flow_n_bytes (" + str(flow_n_bytes) + ") = mirror_attr_n_bytes (" + str(mirror_attr_n_bytes) + "), passed"

	tap = ovs_vport_tap.Tap(ovs_path, None, br, mirror_iface,
				"0.0.0.0", logfd)
	new_n_pkts, new_n_bytes = tap.get_pkt_stats()

	n_sub_tests = n_sub_tests + 1
	if (curr_n_pkts + n_pkts_sent != new_n_pkts):
		passed = False
		print "curr_n_pkts: " + str(curr_n_pkts) + ", n_pkts_sent: " + str(n_pkts_sent) + " != new_n_pkts: " + str(new_n_pkts) + ", failed"
		return passed, n_sub_tests
	print "ovs-ofctl dump-ports check for n_pkts (" + str(new_n_pkts) + ") on mirror port, passed"

	return passed, n_sub_tests

def pbm_traffic_single__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	dst_vm_name = param['vm_name']
	pbm_dir = param['pbm_dir']
	acl_type = param["acl_type"]
	src_vm_name = param["aux_vm_name"]
	custom_action = param["custom_action"]
	otdtf = param["otdtf"]
	n_sub_tests = 0

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  dst_vm_name)
	if (custom_action != None):
		pbm.set_custom_action(custom_action)
	pbm.local_create(acl_type, pbm_dir)
	pbm.dump(False)
	pbm.show(False)

	dst_port_name, dst_mac, dst_ip, dst_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, dst_vm_name)
	src_port_name, src_mac, src_ip, src_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, src_vm_name)

	n_sub_tests = n_sub_tests + 1
	st_param = {
		'pbm' : pbm,
		'ovs_path' : ovs_path,
		'br': br,
		'logfd': logfd,
		'src_mac': src_mac,
		'src_ip': src_ip,
		'dst_mac': dst_mac,
		'dst_ip': dst_ip,
		'dst_ofp_port': dst_ofp_port,
		'acl_type': acl_type,
		'otdtf': otdtf,
	}
	passed = pbm_traffic_ofproto_trace__(st_param)
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests

	st_param = {
		'pbm' : pbm,
		'ovs_path' : ovs_path,
		'br': br,
		'logfd': logfd,
		'src_mac': src_mac,
		'src_ip': src_ip,
		'dst_mac': dst_mac,
		'dst_ip': dst_ip,
		'src_ofp_port': src_ofp_port,
		'dst_ofp_port': dst_ofp_port,
		'acl_type': acl_type,
		'pbm_dir' : pbm_dir,
		'mirror_id' : mirror_id,
	}
	passed, this_n_sub_tests = pbm_traffic_pkt_out__(st_param)
	n_sub_tests = n_sub_tests + this_n_sub_tests
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests

	pbm.local_destroy()
	return passed, n_sub_tests

def pbm_traffic(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	aux_vm_name = test_args["aux_vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	ovs_vers = test_args["ovs_vers"]
	acl_dirs = [ "Ingress", "Egress" ]
	global testcase_id

	if (ovs_vers == 0x230):
		otdtf = 6
	else:
		otdtf = 3

	if (aux_vm_name == None):
		print "Traffic tests need comma separated VM names (for source and destination)"
		return
	traffic_test_handlers = [
		pbm_traffic_single__,
	]
	for pbm_dir in acl_dirs:
		param = {
			'ovs_path' : ovs_path,
			'br' : br,
			'logfd' : logfd,
			'mirror_id': "9900",
			'mirror_dst_ip': mirror_dst_ip,
			'vm_name': vm_name,
			'aux_vm_name': aux_vm_name,
			'pbm_dir' : pbm_dir,
			'acl_type' : acl_type,
			'custom_action': None,
			'otdtf' : otdtf,
		}
		testcase_desc = "PBM Traffic - " + acl_type + ", Dir: " + pbm_dir
		for traffic_test_handler in traffic_test_handlers:
			test = vca_test.TEST(testcase_id, testcase_desc,
					     traffic_test_handler, param)
			suite.register_test(test)
			test.run()
			suite.assert_test_result(test)
			testcase_id = testcase_id + 1
	return

def pbm_redirect_target__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "9999"

	passed, this_n_sub_tests = pbm_single_mirror__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect_allow__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "allow"

	passed, this_n_sub_tests = pbm_single_mirror__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect_fc_override__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "fc_override"

	passed, this_n_sub_tests = pbm_single_mirror__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect_target_traffic__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "9999"
	ovs_vers = param["ovs_vers"]

	if (ovs_vers == 0x230):
		param["otdtf"] = 6
	else:
		param["otdtf"] = 3

	passed, this_n_sub_tests = pbm_traffic_single__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect_allow_traffic__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "allow"
	ovs_vers = param["ovs_vers"]

	if (ovs_vers == 0x230):
		param["otdtf"] = 6
	else:
		param["otdtf"] = 3

	passed, this_n_sub_tests = pbm_traffic_single__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect_fc_override_traffic__(param):
	n_sub_tests = 0
	passed = True
	param["custom_action"] = "fc_override"
	ovs_vers = param["ovs_vers"]

	if (ovs_vers == 0x230):
		param["otdtf"] = 7
	else:
		param["otdtf"] = 4

	passed, this_n_sub_tests = pbm_traffic_single__(param);
	n_sub_tests = this_n_sub_tests + 1
	return passed, n_sub_tests

def pbm_redirect(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	aux_vm_name = test_args["aux_vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	ovs_vers = test_args["ovs_vers"]
	global testcase_id

	if (aux_vm_name == None):
		print "Traffic tests need comma separated VM names (for source and destination)"
		return
	redirect_tests = [
		{
			'desc' : "action: target output",
			'handler': pbm_redirect_target__,
		},
		{
			'desc' : "action: allow",
			'handler': pbm_redirect_allow__,
		},
		{
			'desc' : "action: fc_override",
			'handler': pbm_redirect_fc_override__,
		},
		{
			'desc' : "traffic: target output",
			'handler': pbm_redirect_target_traffic__,
		},
		{
			'desc': "traffic: allow",
			'handler': pbm_redirect_allow_traffic__,
		},
		{
			'desc' : "traffic: fc_override",
			'handler': pbm_redirect_fc_override_traffic__,
		},
	]
	param = {
		'ovs_path' : ovs_path,
		'br' : br,
		'logfd' : logfd,
		'mirror_id': "9900",
		'mirror_dst_ip': mirror_dst_ip,
		'vm_name': vm_name,
		'aux_vm_name': aux_vm_name,
		'pbm_dir' : None,
		'vpm_dir' : None,
		'acl_type' : acl_type,
		'ovs_vers' : ovs_vers,
	}
	for redirect_test in redirect_tests:
		this_test_desc = redirect_test['desc']
		this_test_handler = redirect_test['handler']
		testcase_desc = "PBM Redirect ACL - " + this_test_desc
		test = vca_test.TEST(testcase_id, testcase_desc,
				     this_test_handler, param)
		suite.register_test(test)
		test.run()
		suite.assert_test_result(test)
		testcase_id = testcase_id + 1
	return

def run_pbm(br, vm_name, aux_vm_name, mirror_dst_ip,
	    logfd, ovs_path, ovs_vers, exit_on_failure):
	global testcase_id
	suite = vca_test.SUITE("PBM")
	suite.set_exit_on_failure(exit_on_failure)
	test_handlers = [
		pbm_single_mirror,
		pbm_multiple_acl_mirrors,
		pbm_vpm_single_mirror,
		pbm_traffic,
	]
	types = [ "default", "static", "reflexive", ]
	testcase_id = 1
	suite.print_header()
	for type in types:
		test_args = {
			"suite" : suite,
			"ovs_path" : ovs_path,
			"br" : br,
			"logfd" : logfd,
			"vm_name": vm_name,
			"aux_vm_name" : aux_vm_name,
			"mirror_dst_ip" : mirror_dst_ip,
			"type" : type,
			"ovs_vers" : ovs_vers,
		}
		suite.run(test_handlers, test_args)
	test_handlers = [
		pbm_redirect,
	]
	test_args = {
		"suite" : suite,
		"ovs_path" : ovs_path,
		"br" : br,
		"logfd" : logfd,
		"vm_name": vm_name,
		"aux_vm_name" : aux_vm_name,
		"mirror_dst_ip" : mirror_dst_ip,
		"type" : "Redirect",
		"ovs_vers" : ovs_vers,
	}
	suite.run(test_handlers, test_args)
	suite.print_summary()

################################# VPM ########################################
def vpm_single_mirror__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	mirror_dir = param['vpm_dir']
	n_sub_tests = 0

	vpm = vca_vpm.VPM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	vpm.local_create(mirror_dir)
	vpm.dump(False)
	vpm.show(False)
	mobjs = [ vpm ]
	param['nrefs'] = "1"
	passed, n_this_sub_tests = mirror_verify_all__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	vpm.local_destroy()
	st_param = {	'mirror_obj' : vpm,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def vpm_single_mirror(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	mirror_dst_ip = test_args["mirror_dst_ip"]
	acl_type = test_args["type"]
	global testcase_id
	mirror_dirs = [ "Ingress", "Egress" ]

	for mirror_dir in mirror_dirs:
		param = { 'ovs_path' : ovs_path,
			  'br' : br,
			  'logfd' : logfd,
			  'mirror_id': "9900",
			  'mirror_dst_ip': mirror_dst_ip,
			  'vm_name': vm_name,
			  'vpm_dir' : mirror_dir,
			  'pbm_dir' : None,
			  'acl_type' : None,
			}
		testcase_desc = "Port Mirror: " + mirror_dir
		test = vca_test.TEST(testcase_id, testcase_desc,
				     vpm_single_mirror__, param)
		suite.register_test(test)
		test.run()
		suite.assert_test_result(test)
		testcase_id = testcase_id + 1
	return

def run_vpm(br, vm_name, aux_vm_name, mirror_dst_ip,
	    logfd, ovs_path, ovs_vers, exit_on_failure):
	global testcase_id
	suite = vca_test.SUITE("VPM")
	suite.set_exit_on_failure(exit_on_failure)
	test_handlers = [
		vpm_single_mirror,
	]
	test_args = {
		"suite" : suite,
		"ovs_path" : ovs_path,
		"br" : br,
		"logfd" : logfd,
		"vm_name": vm_name,
		"aux_vm_name" : aux_vm_name,
		"mirror_dst_ip" : mirror_dst_ip,
		"type" : None,
		"ovs_vers" : ovs_vers,
	}
	testcase_id = 1
	suite.print_header()
	suite.run(test_handlers, test_args)
	suite.print_summary()

################################### DYN ######################################
def dyn_verify_mirror_vport__(param):
	mobj = param['mirror_obj']
	vm_name = param['vm_name']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	in_port_name, dst_mac, dst_ip, dst_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, vm_name)
	mobj_port_name = str(mobj.get_port_name())
	if (in_port_name != mobj_port_name):
		print "Mirror vport name verification failed (expected: " + in_port_name + ", got: " + mobj_port_name + ")"
		return False
	else :
		print "Mirror port name verification passed"
	return True

def dyn_verify_agent__(param):
	mobj = param['mirror_obj']
	in_dyn_agent = param['dyn_agent']
	mobj_dyn_agent = str(mobj.get_dyn_agent())
	if (in_dyn_agent != mobj_dyn_agent):
		print "Mirror Dyn Agent verification failed (expected: " + in_dyn_agent + ", got: " + mobj_dyn_agent + ")"
		return False
	else :
		print "Mirror agent name verification passed"
	return True

def mirror_verify_dyn__(mobjs, param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst = param['mirror_dst_port']
	vm_name = param['vm_name']
	nrefs = param['nrefs']
	dyn_agent = param['dyn_agent']
	passed = True
	n_sub_tests = 0

	for mobj in mobjs:
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst' : mirror_dst,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_destination__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'mirror_nrefs' : nrefs,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_nrefs__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'vm_name' : vm_name,
				'ovs_path': ovs_path,
				'br': br,
				'logfd': logfd,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = dyn_verify_mirror_vport__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'dyn_agent': dyn_agent,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = dyn_verify_agent__(st_param)
		if (passed == False):
			break
	return passed, n_sub_tests

def dyn_mirror_single_provisioning__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	dyn_agent = param['dyn_agent']
	n_sub_tests = 0

	dyn = vca_dyn.DYN(ovs_path, br, logfd, mirror_id, mirror_dst_port,
			  vm_name, dyn_agent)
	dyn.local_create()
	dyn.dump(False)
	dyn.show(False)
	mobjs = [ dyn ]
	param['nrefs'] = "0"
	passed, n_this_sub_tests = mirror_verify_dyn__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests

	passed, n_this_sub_tests = mirror_verify_dpi__(dyn, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests

	dyn.local_destroy()
	st_param = {	'mirror_obj' : dyn,
			'ovs_path' : ovs_path,
			'mirror_dst_ip' : mirror_dst_ip,
			'mirror_dst_port' : mirror_dst_port,
	}
	n_sub_tests = n_sub_tests + 1
	passed, n_this_sub_tests = mirror_verify_cleanup__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests


def dyn_traffic_pkt_out_onward__(param):
	passed = True
	n_sub_tests = 0
	dyn = param['dyn']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	src_ofp_port = param['src_ofp_port']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	vrf_id = hex(int(param['vrf_id']))
	n_pkts_sent = int(10)

	mirror_iface = dyn.get_destination()
	if (mirror_iface == None):
		passed = False
		print "Failed to parse mirror interface"
		return passed, n_sub_tests

	cmd = [ ovs_path + "/ovs-appctl", "bridge/clear-flow-stats", br ]
	shell.execute(cmd)
	mac_1 = src_mac
	ip_1 = src_ip
	mac_2 = dst_mac
	ip_2 = dst_ip
	ofp_port = src_ofp_port

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")
	n_flows, n_pkts_in, n_bytes_in, flow_in = dyn.get_flow_pkt_counters(
						"Ingress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_in != n_pkts_sent):
		print "Ingress dyn mirror packet count test: n_pkts_in (" + str(n_pkts_in) + ") != n_pkts_sent (" + str(n_pkts_sent) + ")"
		passed = False
		return passed, n_sub_tests
	print "Onward - Ingress dyn mirror packet count test: passed"

	n_flows, n_pkts_eg, n_bytes_eg, flow_eg = dyn.get_flow_pkt_counters(
						"Egress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_eg != 0):
		print "Egress dyn mirror packet count is non-zero (" + str(n_pkts_eg) + ", failed"
		passed = False
		return passed, n_sub_tests
	print "Onward - Egress dyn mirror packet count zero test: passed"

	n_sub_tests = n_sub_tests + 1
	n_flows_t, n_pkts_t, n_bytes_t, flow_t = dyn.get_flow_pkt_counters_template("Egress", vrf_id)
	if (n_pkts_t != 0):
		print "Onward - Egress create_dyn_mirror packet count (" + str(n_pkts_t) + "), != expected (" + str(0) + "), " + flow_t
	else:
		print "Onward - Egress create_dyn_mirror packet count sanity test: passed"

	actions, flow = dyn.get_flow_mirror_actions("Ingress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (actions == None):
		passed = False
		print "Onward - Mirror flow actions are NULL, failed" + flow
		return passed, n_sub_tests
	print "Onward - Mirror flow actions are non-NULL, passed"
	n_sub_tests = n_sub_tests + 1
	if (actions.find("output") < 0) or (actions.find("resubmit") < 0):
		passed = False
		print "Onward - Mirror flow donot contain output or resubmit at ingress, failed" + flow
		return passed, n_sub_tests
	print "Onward - Mirror flow contain output and resubmit actions at ingress, passed"
	output_ofp_port = dyn.get_flow_mirror_actions_output("Ingress", ofp_port)
	tap = ovs_vport_tap.Tap(ovs_path, "system", br, mirror_dst_port,
				"0.0.0.0", logfd)
	ovs_ofp_port = str(tap.get_ofp_port())
	n_sub_tests = n_sub_tests + 1
	if (output_ofp_port != ovs_ofp_port):
		passed = False
		print "Onward - Mirror flow output (" + output_ofp_port + ") != ovs ofp_port (" + ovs_ofp_port + "), failed"
		return passed, n_sub_tests
	print "Onward - Mirror flow output (" + output_ofp_port + ") matches with ovs ofp_port, passed"

	resub_table = dyn.get_flow_mirror_actions_resub_table("Ingress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (resub_table != "7"):
		passed = False
		print "Onward - Mirror flow shows wrong resubmit table (" + resub_table + "), failed"
		return passed, n_sub_tests
	print "Onward - Mirror flow resubmit table (" + resub_table + ") check, passed"

	n_flows_in, n_pkts_in, n_bytes_in, flow_in = dyn.get_flow_pkt_counters(
						"Ingress", "-1")
	exp_n_flows_tbl5_prio_0 = 1
	exp_n_flows_tbl5_prio_1 = 1
	exp_n_flows_tbl5_prio_2 = 1
	exp_n_flows_tbl5_prio_16384 = 1
	exp_n_flows_tbl5_total = exp_n_flows_tbl5_prio_0 + exp_n_flows_tbl5_prio_1 + exp_n_flows_tbl5_prio_2 + exp_n_flows_tbl5_prio_16384
	n_sub_tests = n_sub_tests + 1
	if (n_flows_in != exp_n_flows_tbl5_total):
		passed = False
		print "Onward - Ingress Mirror Table flow count (" + str(n_flows_in) + ") != expected (" + str(exp_n_flows_tbl5_total) + "), failed"
		return passed, n_sub_tests
	print "Onward - Ingress Mirror Table flow count (" + str(exp_n_flows_tbl5_total) + "), passed"

	n_flows_eg, n_pkts_eg, n_bytes_eg, flow_eg = dyn.get_flow_pkt_counters(
						"Egress", "-1")
	exp_n_flows_tbl6_prio_0 = 1
	exp_n_flows_tbl6_prio_2 = 1
	exp_n_flows_tbl6_total = exp_n_flows_tbl6_prio_0 + exp_n_flows_tbl6_prio_2
	n_sub_tests = n_sub_tests + 1
	if (n_flows_eg != exp_n_flows_tbl6_total):
		if (n_flows_eg != exp_n_flows_tbl6_prio_0):
			passed = False
			print "Onward - Egress Mirror Table flow count (" + str(n_flows_eg) + ") != expected (" + str(exp_n_flows_tbl6_total) + "), failed"
			return passed, n_sub_tests
	print "Onward - Egress Mirror Table flow count (" + str(exp_n_flows_tbl6_total) + "), passed"

	return passed, n_sub_tests

def dyn_mirror_single_traffic_onward__(dyn, param):
	passed = True
	n_sub_tests = 0
	dyn_agent = param['dyn_agent']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	src_vm_name = param['vm_name']
	dst_vm_name = param['aux_vm_name']
	remote_ovs_ip = param['remote_ovs_ip']

	dst_port_name, dst_mac, dst_ip, dst_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, dst_vm_name)
	src_port_name, src_mac, src_ip, src_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, src_vm_name)
	st_param = {
		'dyn' : dyn,
		'ovs_path' : ovs_path,
		'br': br,
		'logfd': logfd,
		'src_mac': src_mac,
		'src_ip': src_ip,
		'dst_mac': dst_mac,
		'dst_ip': dst_ip,
		'src_ofp_port': src_ofp_port,
		'dst_ofp_port': dst_ofp_port,
		'mirror_id' : mirror_id,
		'mirror_dst_port' : mirror_dst_port,
		'dyn_agent': dyn_agent,
		'vrf_id': vrf_id,
	}
	print 
	print "Running onward traffic test with " + dst_port_name + ", ofp_port: " + str(dst_ofp_port)
	passed, n_this_sub_tests = dyn_traffic_pkt_out_onward__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests

	passed, n_this_sub_tests = dpi_traffic_pkt_out_onward__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests
	return passed, n_sub_tests

def dyn_traffic_pkt_out_return__(param):
	passed = True
	n_sub_tests = 0
	dyn = param['dyn']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	src_ofp_port = param['src_ofp_port']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	vrf_id = hex(int(param['vrf_id']))
	n_pkts_sent = int(10)

	mirror_iface = dyn.get_destination()
	if (mirror_iface == None):
		passed = False
		print "Failed to parse mirror interface"
		return passed, n_sub_tests

	cmd = [ ovs_path + "/ovs-appctl", "bridge/clear-flow-stats", br ]
	shell.execute(cmd)
	mac_1 = src_mac
	ip_1 = src_ip
	mac_2 = dst_mac
	ip_2 = dst_ip
	ofp_port = src_ofp_port

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")

	n_flows, n_pkts_in, n_bytes_in, flow_in = dyn.get_flow_pkt_counters(
						"Egress", vrf_id)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_in != n_pkts_sent):
		print "Egress dyn mirror packet count test: n_pkts_in (" + str(n_pkts_in) + ") != n_pkts_sent (" + str(n_pkts_sent) + ")"
		passed = False
		return passed, n_sub_tests
	print "Return - Egress dyn mirror packet count test: passed"

	n_flows, n_pkts_eg, n_bytes_eg, flow_eg = dyn.get_flow_pkt_counters(
						"Ingress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_eg != 0):
		print "Return - Ingress dyn mirror packet count is non-zero (" + str(n_pkts_eg) + ", failed"
		passed = False
		return passed, n_sub_tests
	print "Return - Ingress dyn mirror packet count zero test: passed"

	n_sub_tests = n_sub_tests + 1
	n_flows_t, n_pkts_t, n_bytes_t, flow_t = dyn.get_flow_pkt_counters_template("Ingress", dst_ofp_port)
	if (n_pkts_t != 0):
		print "Return - Ingress create_dyn_mirror packet count (" + str(n_pkts_t) + "), != expected (" + str(0) + "), " + flow_t
	else:
		print "Return - Egress create_dyn_mirror packet count sanity test: passed"

	actions, flow = dyn.get_flow_mirror_actions("Egress", vrf_id)
	n_sub_tests = n_sub_tests + 1
	if (actions == None):
		passed = False
		print "Return - Mirror flow actions are NULL, failed" + flow
		return passed, n_sub_tests
	print "Return - Mirror flow actions are non-NULL, passed"
	n_sub_tests = n_sub_tests + 1
	if (actions.find("output") < 0):
		passed = False
		print "Return - Mirror flow donot contain output at egress, failed, " + flow
		return passed, n_sub_tests
	print "Return - Mirror flow contain output action at egress, passed"

	n_sub_tests = n_sub_tests + 1
	if (actions.find("resubmit") >= 0):
		passed = False
		print "Return - Mirror flow contains output at egress, failed, " + flow
		return passed, n_sub_tests
	print "Return - Mirror flow donot contain contains resubmit action at egress, passed"

	output_ofp_port = dyn.get_flow_mirror_actions_output("Egress", vrf_id)
	tap = ovs_vport_tap.Tap(ovs_path, "system", br, mirror_dst_port,
				"0.0.0.0", logfd)
	ovs_ofp_port = str(tap.get_ofp_port())
	n_sub_tests = n_sub_tests + 1
	if (output_ofp_port != ovs_ofp_port):
		passed = False
		print "Return - Mirror flow output (" + output_ofp_port + ") != ovs ofp_port (" + ovs_ofp_port + "), failed"
		return passed, n_sub_tests
	print "Return - Mirror flow output (" + output_ofp_port + ") matches with ovs ofp_port, passed"

	n_flows_eg, n_pkts, n_bytes, flow = dyn.get_flow_pkt_counters(
						"Egress", "-1")
	exp_n_flows_tbl6_prio_0 = 1
	exp_n_flows_tbl6_prio_1 = 0
	exp_n_flows_tbl6_prio_2 = 1
	exp_n_flows_tbl6_prio_16384 = 1
	exp_n_flows_tbl6_total = exp_n_flows_tbl6_prio_0 + exp_n_flows_tbl6_prio_1 + exp_n_flows_tbl6_prio_2 + exp_n_flows_tbl6_prio_16384
	n_sub_tests = n_sub_tests + 1
	if (n_flows_eg != exp_n_flows_tbl6_total):
		passed = False
		print "Return - Egress Mirror Table flow count (" + str(n_flows_eg) + ") != expected (" + str(exp_n_flows_tbl6_total) + "), failed"
		return passed, n_sub_tests
	print "Return - Egress Mirror Table flow count (" + str(exp_n_flows_tbl6_total) + "), passed"

	n_flows_in, n_pkts, n_bytes, flow = dyn.get_flow_pkt_counters(
						"Ingress", "-1")
	exp_n_flows_tbl5_prio_0 = 1
	exp_n_flows_tbl5_prio_1 = 1
	exp_n_flows_tbl5_prio_2 = 1	# due to onward traffic
	exp_n_flows_tbl5_prio_16384 = 1	# due to onward traffic
	exp_n_flows_tbl5_total = exp_n_flows_tbl5_prio_0 + exp_n_flows_tbl5_prio_1 + exp_n_flows_tbl5_prio_2 + exp_n_flows_tbl5_prio_16384
	n_sub_tests = n_sub_tests + 1
	if (n_flows_in != exp_n_flows_tbl5_total):
		passed = False
		print "Return - Ingress Mirror Table flow count (" + str(n_flows_in) + ") != expected (" + str(exp_n_flows_tbl5_total) + "), failed"
		return passed, n_sub_tests
	print "Return - Ingress Mirror Table flow count (" + str(exp_n_flows_tbl5_total) + "), passed"

	return passed, n_sub_tests

def dyn_mirror_single_traffic_return__(dyn, param):
	passed = True
	n_sub_tests = 0
	dyn_agent = param['dyn_agent']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	src_vm_name = param['vm_name']
	dst_vm_name = param['aux_vm_name']
	remote_ovs_ip = param['remote_ovs_ip']

	if (remote_ovs_ip == None):
		print "Remote ovs_ip is not specified, return traffic tests not ran"
		return passed, n_sub_tests

	tunnel_port, tnl_mac, tnl_ip, tnl_ofp_port = get_tunnel_attr__(ovs_path, br, logfd, remote_ovs_ip)
	src_port_name, src_mac, src_ip, src_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, src_vm_name)
	if (tunnel_port == None):
		print "Tunnel port not found for " + remote_ovs_ip
		return passed, n_sub_tests

	print 
	print "Running return traffic test with " + tunnel_port + ", ofp_port: " + str(tnl_ofp_port) + ", vrf_id: " + str(vrf_id)
	st_param = {
		'dyn' : dyn,
		'ovs_path' : ovs_path,
		'br': br,
		'logfd': logfd,
		'src_mac': tnl_mac,
		'src_ip': tnl_ip,
		'src_ofp_port': tnl_ofp_port,
		'dst_mac': src_mac,
		'dst_ip': src_ip,
		'dst_ofp_port': src_ofp_port,
		'mirror_id' : mirror_id,
		'mirror_dst_port' : mirror_dst_port,
		'vrf_id': vrf_id,
		'dyn_agent': dyn_agent,
	}
	passed, n_this_sub_tests = dyn_traffic_pkt_out_return__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests

	passed, n_this_sub_tests = dpi_traffic_pkt_out_return__(st_param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests
	return passed, n_sub_tests

def dyn_traffic_cleanup__(dyn):
	passed = True
	n_sub_tests = 0

	n_flows_in, n_pkts_in, n_bytes_in, flow_in = dyn.get_flow_pkt_counters(
						"Ingress", "-1")
	exp_n_flows_tbl5_prio_0 = 1
	exp_n_flows_tbl5_total = exp_n_flows_tbl5_prio_0
	n_sub_tests = n_sub_tests + 1
	if (n_flows_in != exp_n_flows_tbl5_total):
		passed = False
		print "Flow cleanup check - Ingress Mirror Table (" + str(n_flows_in) + ") != expected (" + str(exp_n_flows_tbl5_total) + "), failed"
		return passed, n_sub_tests
	print "Flow cleanup check - Ingress Mirror Table (" + str(exp_n_flows_tbl5_total) + "), passed"

	n_flows_eg, n_pkts_eg, n_bytes_eg, flow_eg = dyn.get_flow_pkt_counters(
						"Egress", "-1")
	exp_n_flows_tbl6_prio_0 = 1
	exp_n_flows_tbl6_prio_1 = 1
	exp_n_flows_tbl6_total = exp_n_flows_tbl6_prio_0 + exp_n_flows_tbl6_prio_1
	n_sub_tests = n_sub_tests + 1
	if (n_flows_eg != exp_n_flows_tbl6_total):
		if (n_flows_eg != exp_n_flows_tbl6_prio_0):
			passed = False
			print "Flow cleanup check - Egress Mirror Table (" + str(n_flows_eg) + ") != expected (" + str(exp_n_flows_tbl6_total) + "), failed"
			return passed, n_sub_tests
	print "Flow cleanup check - Egress Mirror Table (" + str(exp_n_flows_tbl6_total) + "), passed"
	return passed, n_sub_tests

def dyn_mirror_single_traffic__(param):
	passed = True
	n_sub_tests = 0
	n_this_sub_tests = 0
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	dyn_agent = param['dyn_agent']
	src_vm_name = param['vm_name']
	dst_vm_name = param['aux_vm_name']
	remote_ovs_ip = param['remote_ovs_ip']

	print "Dyn Mirror Traffic Test - " + dyn_agent

	dyn = vca_dyn.DYN(ovs_path, br, logfd, mirror_id, mirror_dst_port,
			  src_vm_name, dyn_agent)
	dyn.local_create()
	dyn.dump(False)
	dyn.show(False)

	passed, n_this_sub_tests = dyn_mirror_single_traffic_onward__(dyn,
								      param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		dyn.local_destroy()
		return passed, n_sub_tests

	passed, n_this_sub_tests = dyn_mirror_single_traffic_return__(dyn,
								      param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		dyn.local_destroy()
		return passed, n_sub_tests

	dyn.local_destroy()

	passed, n_this_sub_tests = dyn_traffic_cleanup__(dyn)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def dyn_mirror_flow_mod_onward__(dyn, param):
	passed = True
	n_sub_tests = 0
	dyn_agent = param['dyn_agent']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	src_vm_name = param['vm_name']
	dst_vm_name = param['aux_vm_name']
	remote_ovs_ip = param['remote_ovs_ip']
	n_pkts_sent = int(10)
	ofreg_str = "NXM_NX_REG5"
	add_reg_name = "reg5"
	add_reg_val = "100"
	del_reg_name = "reg12"
	del_reg_val = "0"

	dst_port_name, dst_mac, dst_ip, dst_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, dst_vm_name)
	src_port_name, src_mac, src_ip, src_ofp_port, vrf_id = get_vm_attr__(
			ovs_path, br, logfd, src_vm_name)
	mirror_iface = dyn.get_destination()
	if (mirror_iface == None):
		passed = False
		print "Failed to parse mirror interface"
		return passed, n_sub_tests

	cmd = [ ovs_path + "/ovs-appctl", "bridge/clear-flow-stats", br ]
	shell.execute(cmd)
	mac_1 = src_mac
	ip_1 = src_ip
	mac_2 = dst_mac
	ip_2 = dst_ip
	ofp_port = src_ofp_port

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")

	print
	print "Adding reg modification action to Ingress Mirror Table rule"
	actions, n_pkts_org, n_pkts_new = dyn.set_flow_reg("Ingress", ofp_port,
		       					   src_port_name,
							   add_reg_name,
							   add_reg_val)
	n_sub_tests = n_sub_tests + 1
	if (actions == None or n_pkts_org == None or n_pkts_new == None):
		passed = False
		print "Onward - mod-flows reg-add test #1, actions: " + actions + ", n_pkts_org: " + n_pkts_org + ", n_pkts_new: " + n_pkts_new + ", failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #1 - non NULL actions, passed"

	n_sub_tests = n_sub_tests + 1
	if (n_pkts_org != str(n_pkts_sent)):
		passed = False
		print "Onward - mod-flows reg-add test #2, n_pkts_org (" + n_pkts_org + ") != n_pkts_sent (" + str(n_pkts_sent) + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #2 - n_pkts_org = n_pkts_sent, passed"

	n_sub_tests = n_sub_tests + 1
	exp_n_pkts_new = int(0)
	if (n_pkts_new != str(exp_n_pkts_new)):
		passed = False
		print "Onward - mod-flows reg-add test #3, n_pkts_new (" + n_pkts_new + ") != exp_n_pkts_new (" + str(exp_n_pkts_new) + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #3 - n_pkts_new = " + str(exp_n_pkts_new) + ", passed"

	n_sub_tests = n_sub_tests + 1
	actions_has_load = actions.find("load") >= 0
	if (actions_has_load == False):
		passed = False
		print "Onward - mod-flows reg-add test #4: no load" + actions
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #4: " + actions

	n_sub_tests = n_sub_tests + 1
	actions_has_ofreg_str = actions.find(ofreg_str) >= 0
	if (actions_has_ofreg_str == False):
		passed = False
		print "Onward - mod-flows reg-add test #5: expected (" + ofreg_str + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #5: openflow reg5 check"

	n_sub_tests = n_sub_tests + 1
	load_str = actions.split("->")
	if (load_str == None):
		passed = False
		print "Onward - mod-flows reg-add test #6: NULL load_str, failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #6: load_str non-null, passed"

	n_sub_tests = n_sub_tests + 1
	new_reg_val = load_str[0].split(":")[1]
	if (new_reg_val != hex(int(add_reg_val))):
		passed = False
		print "Onward - mod-flows reg-add test #7: register value: expected (" + add_reg_val + "), got: (" + new_reg_val + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add test #7: register value sanity (" + add_reg_val + ") check, passed"

	n_sub_tests = n_sub_tests + 1
	has_resubmit = actions.find("resubmit") >= 0
	if (has_resubmit == False):
		passed = False
		print "Onward - mod-flows reg-add missing resubmit action"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add has resubmit action, passed"

	has_output = actions.find("output") >= 0
	n_sub_tests = n_sub_tests + 1
	if (has_output == False):
		passed = False
		print "Onward - mod-flows reg-add missing output action"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-add has output action, passed"

	param['op'] = "reg-add"
	passed, n_this_sub_tests = dpi_flow_mod_onward__(dyn, actions, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests

	print
	print "Traffic test after modifying mirror actions"
	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")
	n_flows_in, n_pkts_in, n_bytes_in, flow_in = dyn.get_flow_pkt_counters(
						"Ingress", ofp_port)
	n_sub_tests = n_sub_tests + 1
	if (str(n_pkts_in) != str(n_pkts_sent)):
		print "Onward - unable to mirror packets upon flow modification, n_pkts_in: " + str(n_pkts_in) + ", failed"
		passed = False
		return passed, n_sub_tests
	print "Onward - mirror packets upon flow modification, passed"

	print
	print "Deleting reg modification action from Ingress Mirror Table rule"
	actions, n_pkts_org, n_pkts_new = dyn.set_flow_reg("Ingress", ofp_port,
		       					   src_port_name,
							   del_reg_name,
							   del_reg_val)
	n_sub_tests = n_sub_tests + 1
	if (actions == None or n_pkts_org == None or n_pkts_new == None):
		passed = False
		print "Onward - mod-flows reg-del test #1, actions: " + actions + ", n_pkts_org: " + n_pkts_org + ", n_pkts_new: " + n_pkts_new + ", failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #1 - non NULL actions, passed"

	n_sub_tests = n_sub_tests + 1
	if (n_pkts_org != str(n_pkts_sent)):
		passed = False
		print "Onward - mod-flows reg-del test #2, n_pkts_org (" + n_pkts_org + ") != n_pkts_sent (" + str(n_pkts_sent) + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #2 - n_pkts_org = n_pkts_sent, passed"

	n_sub_tests = n_sub_tests + 1
	exp_n_pkts_new = int(0)
	if (n_pkts_new != str(exp_n_pkts_new)):
		passed = False
		print "Onward - mod-flows reg-del test #3, n_pkts_new (" + n_pkts_new + ") != exp_n_pkts_new (" + str(exp_n_pkts_new) + "), failed"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #3 - n_pkts_new = " + str(exp_n_pkts_new) + ", passed"

	n_sub_tests = n_sub_tests + 1
	actions_has_load = actions.find("load") >= 0
	if (actions_has_load == True):
		passed = False
		print "Onward - mod-flows reg-del test #4: still load present, " + actions
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #4 successfully deleted reg action, passed"

	n_sub_tests = n_sub_tests + 1
	has_resubmit = actions.find("resubmit") >= 0
	if (has_resubmit == False):
		passed = False
		print "Onward - mod-flows reg-del missing resubmit action"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #5 has resubmit action, passed"

	has_output = actions.find("output") >= 0
	n_sub_tests = n_sub_tests + 1
	if (has_output == False):
		passed = False
		print "Onward - mod-flows reg-del missing output action"
		return passed, n_sub_tests
	print "Onward - mod-flows reg-del test #6 has output action, passed"

	param['op'] = "reg-del"
	passed, n_this_sub_tests = dpi_flow_mod_onward__(dyn, actions, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		return passed, n_sub_tests
	return passed, n_sub_tests

def dyn_mirror_flow_mod_return__(dyn, param):
	passed = True
	n_sub_tests = 0
	return passed, n_sub_tests

def dyn_mirror_flow_mod__(param):
	passed = True
	n_sub_tests = 0
	n_this_sub_tests = 0
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_port = param['mirror_dst_port']
	dyn_agent = param['dyn_agent']
	src_vm_name = param['vm_name']
	dst_vm_name = param['aux_vm_name']
	remote_ovs_ip = param['remote_ovs_ip']

	print "Dyn Mirror Flow Modification Test - " + dyn_agent

	dyn = vca_dyn.DYN(ovs_path, br, logfd, mirror_id, mirror_dst_port,
			  src_vm_name, dyn_agent)
	dyn.local_create()
	dyn.dump(False)
	dyn.show(False)

	passed, n_this_sub_tests = dyn_mirror_flow_mod_onward__(dyn, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		dyn.local_destroy()
		return passed, n_sub_tests

	passed, n_this_sub_tests = dyn_mirror_flow_mod_return__(dyn, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		dyn.local_destroy()
		return passed, n_sub_tests

	dyn.local_destroy()

	passed, n_this_sub_tests = dyn_traffic_cleanup__(dyn)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	return passed, n_sub_tests

def dyn_single_mirror(test_args):
	global testcase_id
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	vm_name = test_args["vm_name"]
	aux_vm_name = test_args["aux_vm_name"]
	mirror_dst_port = test_args["mirror_dst_port"]
	remote_ovs_ip = test_args["remote_ovs_ip"]
	mirror_dst_ip = "0.0.0.0"
	pbm_dir = "n/a"
	vpm_dir = "n/a"
	acl_type = "n/a"
	agents = [
       		{
			'dyn_agent': "dyn-mirror",
			'mirror_dst': mirror_dst_port,
		},
       		{
			'dyn_agent': "dpi",
			'mirror_dst': "svc-dpi-tap",
		},
	]
	dyn_single_mirror_tests = [
		{
			'handler' : dyn_mirror_single_provisioning__,
			'desc' : "provisioning",
		},
		{
			'handler' : dyn_mirror_single_traffic__,
			'desc' : "traffic",
		},
		{
			'handler' : dyn_mirror_flow_mod__,
			'desc' : "flow-modification",
		},
	]
	for a in agents :
		dyn_agent = a['dyn_agent']
		mirror_dst = a['mirror_dst']
		param = { 'ovs_path' : ovs_path,
			  'br' : br,
			  'logfd' : logfd,
			  'mirror_id': "99",
			  'mirror_dst_port': mirror_dst,
			  'mirror_dst_ip': mirror_dst_ip,
			  'remote_ovs_ip': remote_ovs_ip,
			  'vm_name': vm_name,
			  'aux_vm_name': aux_vm_name,
			  'dyn_agent' : dyn_agent,
		}
		for dsm_test in dyn_single_mirror_tests:
			this_desc = dsm_test['desc']
			this_test = dsm_test['handler']
			testcase_desc = "Dynamic Single Mirror - " + this_desc + ": " + dyn_agent
			test = vca_test.TEST(testcase_id, testcase_desc,
					     this_test, param)
			suite.register_test(test)
			test.run()
			suite.assert_test_result(test)
			testcase_id = testcase_id + 1

def run_dyn(br, vm_name, aux_vm_name, mirror_dst_port, remote_ovs_ip,
	    logfd, ovs_path, ovs_vers, exit_on_failure):
	global testcase_id
	suite = vca_test.SUITE("DYN")
	suite.set_exit_on_failure(exit_on_failure)
	test_handlers = [
		dyn_single_mirror,
	]
	test_args = {
		"suite" : suite,
		"ovs_path" : ovs_path,
		"br" : br,
		"logfd" : logfd,
		"vm_name": vm_name,
		"aux_vm_name" : aux_vm_name,
		"mirror_dst_port" : mirror_dst_port,
		"remote_ovs_ip" : remote_ovs_ip,
		"ovs_vers" : ovs_vers,
	}
	testcase_id = 1
	suite.print_header()
	suite.run(test_handlers, test_args)
	suite.print_summary()

################################ DPI (dyn-mirror) ############################
def mirror_verify_dpi__(dyn, param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst = param['mirror_dst_port']
	vm_name = param['vm_name']
	nrefs = param['nrefs']
	dyn_agent = param['dyn_agent']
	passed = True
	n_sub_tests = 0

	if (dyn_agent != "dpi"):
		return passed, n_sub_tests

	mobj_vport, mac, ip, ofp_port, vrf_id = get_vm_attr__(ovs_path, br,
							      logfd, vm_name)
	mobj_mirror_dst = str(dyn.get_destination())

	dpi_vport = str(dyn.get_dpi_port_by_mirror_id(mirror_id))
	dpi_mirror_dst = str(dyn.get_dpi_port_by_mirror_id("-"))

	n_sub_tests = n_sub_tests + 1
	if (dpi_vport != mobj_vport):
		passed = False
		print "Mirror vport check, (got: " + dpi_vport + ", expect: " + mobj_vport + "), failed"
		return passed, n_sub_tests
	print "Mirror vport " + mobj_vport + " listed in dpi/show, passed"

	n_sub_tests = n_sub_tests + 1
	if (dpi_mirror_dst != mobj_mirror_dst):
		passed = False
		print "Mirror destination check, (got: " + dpi_mirror_dst + ", expect: " + mobj_mirror_dst + "), failed"
		return passed, n_sub_tests
	print "Mirror destination " + mobj_mirror_dst + " listed in dpi/show, passed"

	return passed, n_sub_tests

# ['push_vlan:0x8100', 'mod_vlan_vid:99', 'mod_vlan_pcp:0', 'strip_vlan']
def dpi_traffic_pkt_out_action_check__(act, loc, traffic_dir,
	       			       mirror_id, n_sub_tests):
	passed = True
	if (act.find("push_vlan") >= 0):
		n_sub_tests = n_sub_tests + 1
		if (loc != 1):
			passed = False
			print traffic_dir + " - push_vlan action not the first one, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: push_vlan position check passed"
		n_sub_tests = n_sub_tests + 1
		proto = act.split(":")[1]
		if (proto != "0x8100"):
			passed = False
			print traffic_dir + " - push_vlan action protocol not 0x8100, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: push_vlan protocol 0x8100, passed"
	elif (act.find("mod_vlan_vid") >= 0):
		n_sub_tests = n_sub_tests + 1
		if (loc != 2):
			passed = False
			print traffic_dir + " - mod_vlan_vid action not the first one, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: mod_vlan_vid position check passed"
		vid = act.split(":")[1]
		n_sub_tests = n_sub_tests + 1
		if (vid != str(mirror_id)):
			print traffic_dir + " - mod_vlan_vid action (" + vid + ") != mirror_id (" + mirror_id + "), failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: mod_vlan_vid value (" + vid + ") check passed"
	elif (act.find("mod_vlan_pcp") >= 0):
		n_sub_tests = n_sub_tests + 1
		if (loc != 3):
			passed = False
			print traffic_dir + " - mod_vlan_pcp action not the first one, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: mod_vlan_pcp position check passed"
		pcp = act.split(":")[1]
		n_sub_tests = n_sub_tests + 1
		if (pcp != "0"):
			passed = False
			print traffic_dir + " - mod_vlan_pcp action value not 0, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: mod_vlan_pcp value 0, passed"
	elif (act.find("strip_vlan") >= 0):
		n_sub_tests = n_sub_tests + 1
		if (loc != 4):
			passed = False
			print traffic_dir + " - strip_vlan action not the first one, failed"
			return passed, n_sub_tests
		print traffic_dir + " - DPI custom action: strip_vlan position check passed"
	return passed, n_sub_tests

def dpi_traffic_pkt_out_onward__(param):
	passed = True
	n_sub_tests = 0
	dyn = param['dyn']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	src_ofp_port = param['src_ofp_port']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	mirror_id = param['mirror_id']
	dyn_agent = param['dyn_agent']
	n_pkts_sent = int(10)

	if (dyn_agent != "dpi"):
		return passed, n_sub_tests

	curr_n_pkts, curr_n_bytes = dyn.get_dpi_stats_by_mirror_id(mirror_id)
	mac_1 = src_mac
	ip_1 = src_ip
	mac_2 = dst_mac
	ip_2 = dst_ip
	ofp_port = src_ofp_port

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")
	new_n_pkts, new_n_bytes = dyn.get_dpi_stats_by_mirror_id(mirror_id)
	n_pkts_received = int(new_n_pkts) - int(curr_n_pkts)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_received != n_pkts_sent):
		print "Onward - Packets received at DPI port (" + str(n_pkts_received) + ") != sent (" + str(n_pkts_sent), + "), failed"
		passed = False
		return passed, n_sub_tests
	print "Onward - packets received at DPI port matched with sent (" + str(n_pkts_sent) + "), passed"

	vlan_acts = dyn.get_flow_mirror_actions_vlan_opts("Ingress", ofp_port)
	i = int(0)
	n_exp_actions = int(4)
	for act in vlan_acts:
		i = i + 1
		passed, n_sub_tests = dpi_traffic_pkt_out_action_check__(
						act, i, "Onward", mirror_id,
						n_sub_tests)

	n_sub_tests = n_sub_tests + 1
	if (i != n_exp_actions):
		passed = False
		print "Onward - DPI custom action count check failed, expected: " + str(n_exp_actions) + ", got: " + str(i)
	print "Onward - DPI custom action count check (" + str(n_exp_actions) + "), passed"
	return passed, n_sub_tests

def dpi_traffic_pkt_out_return__(param):
	passed = True
	n_sub_tests = 0
	dyn = param['dyn']
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	src_mac = param['src_mac']
	src_ip = param['src_ip']
	src_ofp_port = param['src_ofp_port']
	dst_mac = param['dst_mac']
	dst_ip = param['dst_ip']
	dst_ofp_port = param['dst_ofp_port']
	mirror_id = param['mirror_id']
	dyn_agent = param['dyn_agent']
	vrf_id = hex(int(param['vrf_id']))
	n_pkts_sent = int(10)

	if (dyn_agent != "dpi"):
		return passed, n_sub_tests

	curr_n_pkts, curr_n_bytes = dyn.get_dpi_stats_by_mirror_id(mirror_id)
	mac_1 = src_mac
	ip_1 = src_ip
	mac_2 = dst_mac
	ip_2 = dst_ip
	ofp_port = src_ofp_port

	for i in range(n_pkts_sent):
		net.send_packet(ovs_path, br, i, mac_1, ip_1, mac_2, ip_2,
				ofp_port, "vca-mirror-tests")
	new_n_pkts, new_n_bytes = dyn.get_dpi_stats_by_mirror_id(mirror_id)
	n_pkts_received = int(new_n_pkts) - int(curr_n_pkts)
	n_sub_tests = n_sub_tests + 1
	if (n_pkts_received != n_pkts_sent):
		print "Return - Packets received at DPI port (" + str(n_pkts_received) + ") != sent (" + str(n_pkts_sent), + "), failed"
		passed = False
		return passed, n_sub_tests
	print "Return - packets received at DPI port matched with sent (" + str(n_pkts_sent) + "), passed"

	vlan_acts = dyn.get_flow_mirror_actions_vlan_opts("Egress", vrf_id)
	i = int(0)
	n_exp_actions = int(4)
	if (vlan_acts != None):
		for act in vlan_acts:
			i = i + 1
			passed, n_sub_tests = dpi_traffic_pkt_out_action_check__(
						act, i, "Return", mirror_id,
						n_sub_tests)

	n_sub_tests = n_sub_tests + 1
	if (i != n_exp_actions):
		passed = False
		print "Return - DPI custom action count check failed, expected: " + str(n_exp_actions) + ", got: " + str(i)
		return passed, n_sub_tests
	print "Return - DPI custom action count check (" + str(n_exp_actions) + "), passed"
	return passed, n_sub_tests

def dpi_flow_mod_onward__(dyn, actions, param):
	passed = True
	n_sub_tests = 0
	dyn_agent = param['dyn_agent']
	op = param['op']
	action_set = [ 'push_vlan', 'strip_vlan', 'mod_vlan_vid', 'mod_vlan_pcp' ]

	if (dyn_agent != "dpi"):
		return passed, n_sub_tests

	for a in action_set:
		has_action = actions.find(a) >= 0
		n_sub_tests = n_sub_tests + 1
		if (has_action == False):
			passed = False
			print "Onward - DPI agent mod-flows " + op + " missing " + a + " action"
			return passed, n_sub_tests
		print "Onward - mod-flows " + op + " has DPI agent custom action (" + a + "), passed"

	return passed, n_sub_tests

############################### MAIN #########################################
def validate_args(progname, suite,
		  vm_name, aux_vm_name,
		  mirror_dst_ip,
		  mirror_dst_port):
	success = True
	if (vm_name == None):
		print progname + ": missing VM name"
		success = False
	elif (vm_name.find("-") == 0):
		print progname + ": option -v requires an argument"
		success = False
	if (suite == "PBM"):
		if (mirror_dst_ip == None):
			print progname + ": missing mirror destination IP for PBM suite"
			success = False
	elif (suite == "VPM"):
		if (mirror_dst_ip == None):
			print progname + ": missing mirror destination IP for VPM suite"
			success = False
	elif (suite == "DYN"):
		if (mirror_dst_port == None):
			print progname + ": missing mirror destination port for DYN suite"
			success = False
	elif (suite == "all"):
		if (mirror_dst_ip == None):
			print progname + ": missing mirror destination IP for all suite"
			success = False
		if (mirror_dst_port == None):
			print progname + ": missing mirror destination port for all suite"
			success = False
	return success

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	global testcase_id
	vm_name = None
	aux_vm_name = None
	mirror_dst_ip = None
	mirror_dst_port = None
	remote_ovs_ip = None
	exit_on_failure = False
	ovs_vers = ovs_helper.get_ovs_version(ovs_path)
	suite_list = [ "all" ]
	try:
		opts, args = getopt.getopt(argv, "hv:i:es:p:r:")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-h":
			usage()
		elif opt == "-v":
			vm_list = arg
			if (arg.find(",") > 0):
				vm_name = arg.split(",")[0]
				aux_vm_name = arg.split(",")[1]
			else:
				vm_name = arg
		elif opt == "-i":
			mirror_dst_ip = arg
		elif opt == "-r":
			remote_ovs_ip = arg
		elif opt == "-p":
			mirror_dst_port = arg
		elif opt == "-e":
			exit_on_failure = True
		elif opt == "-s":
			suite_list = arg.split(",")
		else:
			usage()
	logfd = logger.open_log(logfile)
	for suite in suite_list:
		if (validate_args(progname, suite,
				  vm_name, aux_vm_name, mirror_dst_ip,
				  mirror_dst_port) == False):
			exit(1)
		if (suite == "PBM"):
			run_pbm(br, vm_name, aux_vm_name, mirror_dst_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
		elif (suite == "VPM"):
			run_vpm(br, vm_name, aux_vm_name, mirror_dst_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
		elif (suite == "DYN"):
			run_dyn(br, vm_name, aux_vm_name,
				mirror_dst_port, remote_ovs_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
		else:
			run_pbm(br, vm_name, aux_vm_name, mirror_dst_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
			run_vpm(br, vm_name, aux_vm_name, mirror_dst_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
			run_dyn(br, vm_name, aux_vm_name,
				mirror_dst_port, remote_ovs_ip,
				logfd, ovs_path, ovs_vers, exit_on_failure)
	
	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	testcase_id = 1
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

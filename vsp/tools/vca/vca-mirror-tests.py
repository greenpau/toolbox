#!/usr/bin/python

import sys
import os
import getopt

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
import net

# OVS classes
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_helper
import ovs_vport_tap

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_test
import vca_pbm
import vca_vpm

def usage():
	print "usage: " + progname + " [options]"
	print "options:"
	print "    -v <vm_name>: name of VM whose ACLs/ports are to be mirrored"
	print "    -i <ip>: mirror destination IPv4 address"
	sys.exit(1)

def mirror_verify_dst_ip__(param):
	mobj = param['mirror_obj']
	mirror_dst_ip = param['mirror_dst_ip']
	mobj_dst_ip = str(mobj.get_dst_ip())
	if (mirror_dst_ip != mobj_dst_ip):
		print "Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + mobj_dst_ip + ")"
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

	for mobj in mobjs:
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst_ip' : mirror_dst_ip,
			   }
		passed = mirror_verify_dst_ip__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst_ip' : mirror_dst_ip,
			   }
		passed = mirror_verify_internal_name__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'ovs_path' : ovs_path,
				'br' : br,
				'logfd' : logfd,
			   }
		passed = mirror_verify_tunnel_ofp_port__(st_param)
		if (passed == False):
			break
		st_param = {	'mirror_obj' : mobj,
				'mirror_nrefs' : nrefs,
			   }
		passed = mirror_verify_nrefs__(st_param)
		if (passed == False):
			break
	return passed

def pbm_verify_flow_attrs__(param):
	pbm = param['mirror_obj']
	mirror_dir = param['mirror_dir']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	dir_verified = False
	mirror_attrs = pbm.get_mirror_flow_attrs()
	for mirror_attr in mirror_attrs:
		table_id = mirror_attr['table_id']
		if (table_id == "9"):
			flow_mirror_dir = "ingress"
		elif (table_id == "14"):
			flow_mirror_dir = "egress"
		else:
			print "Flow returned bad table_id: " + table_id
			return False
		flow_mirror_id = mirror_attr['mirror_id']
		flow_mirror_dst_ip = mirror_attr['mirror_dst_ip']
		if (flow_mirror_dir != mirror_dir):
			continue
		else:
			dir_verified = True
			print "Flow Mirror Direction verification passed"
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
	if (dir_verified == False):
		print "Flow Mirror Direction verification failed (expected: " + mirror_dir + ", but not found in dump-detailed-flows" + ")"
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

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	pbm.local_create(acl_type, acl_dir)
	pbm.dump(False)
	pbm.show(False)
	mobjs = [ pbm ]
	param['nrefs'] = "1"
	passed = mirror_verify_all__(mobjs, param)
	if (passed == False):
		pbm.local_destroy()
		return False
	st_param = {	'mirror_obj' : pbm,
			'mirror_dir' : acl_dir,
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	passed = pbm_verify_flow_attrs__(st_param)
	pbm.local_destroy()
	return passed

def pbm_multiple_acl_mirrors__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	acl_type = param['acl_type']

	pbm1 = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			   vm_name)
	pbm1.local_create(acl_type, "ingress")
	pbm1.dump(False)
	pbm1.show(False)
	pbm2 = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			   vm_name)
	pbm2.local_create(acl_type, "egress")
	pbm2.dump(False)
	pbm2.show(False)
	mobjs = [ pbm1, pbm2 ]
	param['nrefs'] = "2"
	passed = mirror_verify_all__(mobjs, param)
	if (passed == False):
		pbm1.local_destroy()
		pbm2.local_destroy()
		return False
	st_param = {	'mirror_obj' : pbm1,
			'mirror_dir' : "ingress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	passed = pbm_verify_flow_attrs__(st_param)
	st_param = {	'mirror_obj' : pbm2,
			'mirror_dir' : "egress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	passed = pbm_verify_flow_attrs__(st_param)
	pbm1.local_destroy()
	pbm2.local_destroy()
	return True

def pbm_single_mirror(ovs_path, br, logfd, vm_name,
		      mirror_dst_ip, acl_type, testcase_id):
	acl_dirs = [ "ingress", "egress" ]

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
			}
		testcase_desc = "Single ACL Mirror: " + acl_dir + " " + acl_type
		test = vca_test.TEST(testcase_id, testcase_desc,
				     pbm_single_mirror__, param)
		test.run()
		testcase_id = testcase_id + 1
	return testcase_id

def pbm_multiple_acl_mirrors(ovs_path, br, logfd, vm_name,
			     mirror_dst_ip, acl_type, testcase_id):
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
	test.run()
	testcase_id = testcase_id + 1
	return testcase_id

def vpm_single_mirror__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	mirror_dir = param['vpm_dir']

	vpm = vca_vpm.VPM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	vpm.local_create(mirror_dir)
	vpm.dump(False)
	vpm.show(False)
	mobjs = [ vpm ]
	param['nrefs'] = "1"
	passed = mirror_verify_all__(mobjs, param)
	vpm.local_destroy()
	return passed

def vpm_single_mirror(ovs_path, br, logfd, vm_name, mirror_dst_ip,
		      testcase_id):
	mirror_dirs = [ "ingress", "egress" ]

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
		test.run()
		testcase_id = testcase_id + 1
	return testcase_id

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
	passed = mirror_verify_all__(mobjs, param)
	if (passed == False):
		vpm.local_destroy()
		pbm.local_destroy()
		return False
	st_param = {	'mirror_obj' : pbm,
			'mirror_dir' : pbm_dir,
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	passed = pbm_verify_flow_attrs__(st_param)
	pbm.local_destroy()
	vpm.local_destroy()
	return passed

def pbm_vpm_single_mirror(ovs_path, br, logfd, vm_name,
			  mirror_dst_ip, acl_type, testcase_id):
	acl_dirs = [ "ingress", "egress" ]
	vpm_dirs = [ "ingress", "egress", "both" ]

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
			test.run()
			testcase_id = testcase_id + 1
	return testcase_id

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	testcase_id = 1
	vm_name = None
	mirror_dst_ip = None
	try:
		opts, args = getopt.getopt(argv, "hv:i:")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-h":
			usage()
		elif opt == "-v":
			vm_name = arg
		elif opt == "-i":
			mirror_dst_ip = arg
		else:
			usage()
	logfd = logger.open_log(logfile)
	if (vm_name == None or mirror_dst_ip == None):
		usage()

	testcase_id = pbm_single_mirror(ovs_path, br,
					logfd, vm_name, mirror_dst_ip,
					"default", testcase_id)
	testcase_id = pbm_multiple_acl_mirrors(ovs_path, br,
					       logfd, vm_name, mirror_dst_ip,
					       "default", testcase_id)
	testcase_id = vpm_single_mirror(ovs_path, br, logfd,
					vm_name, mirror_dst_ip, testcase_id)
	testcase_id = pbm_vpm_single_mirror(ovs_path, br, logfd,
					    vm_name, mirror_dst_ip,
					    "default", testcase_id)

	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

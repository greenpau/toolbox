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

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_test
import vca_pbm
import vca_vpm
import vca_vm

def usage():
	print "usage: " + progname + " [options]"
	print "options:"
	print "    -v <vm_name>: name of VM whose ACLs/ports are to be mirrored"
	print "    -i <ip>: mirror destination IPv4 address"
	print "    -e: exitOnFailure=true"
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
	n_sub_tests = 0

	for mobj in mobjs:
		st_param = {	'mirror_obj' : mobj,
				'mirror_dst_ip' : mirror_dst_ip,
			   }
		n_sub_tests = n_sub_tests + 1
		passed = mirror_verify_dst_ip__(st_param)
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

	mobj_dst_ip = mobj.get_dst_ip()
	n_sub_tests = n_sub_tests + 1
	if (mobj_dst_ip != None):
		print "mirror cleanup check failed"
		return False
	else:
		print "mirror cleanup check passed"

	mirror_tunnel = "t" + net.ipaddr2hex(mirror_dst_ip)
	cmd = [ ovs_path + "/ovs-appctl", "dpif/show" ]
	dpif_show_out = shell.execute(cmd).splitlines()
	n_sub_tests = n_sub_tests + 1
	for line in dpif_show_out:
		if (line.find(mirror_tunnel) >= 0):
			print "mirror tunnel not cleaned up"
			return False
	print "mirror tunnel cleanup check passed"
	return True, n_sub_tests

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

def pbm_verify_mirror_vport__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	vm_name = param['vm_name']
	pbm = param['mirror_obj']
	mirror_dir = param['mirror_dir']

	mirror_vport, mirror_vport_ofp_port, mirror_vport_odp_port = pbm.get_mirror_vport(mirror_dir)
	vm = vca_vm.VM(ovs_path, br, None, None, None, None, None, None,
		       None, None, None, logfd)
	vm.set_vm_name(vm_name)
	vport = vm.vport()
	if (vport == mirror_vport):
		print "Mirror VPORT name verification passed"
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
	n_sub_tests = 0

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
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
			'mirror_obj' : pbm,
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
	passed, n_this_sub_tests = mirror_verify_all__(mobjs, param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		pbm1.local_destroy()
		pbm2.local_destroy()
		return False, n_sub_tests
	st_param = {	'mirror_obj' : pbm1,
			'mirror_dir' : "ingress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
	st_param = {	'mirror_obj' : pbm2,
			'mirror_dir' : "egress",
			'mirror_id' : mirror_id,
			'mirror_dst_ip' : mirror_dst_ip,
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
	acl_dirs = [ "ingress", "egress" ]
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
		   }
	n_sub_tests = n_sub_tests + 1
	passed = pbm_verify_flow_attrs__(st_param)
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
			suite.register_test(test)
			test.run()
			suite.assert_test_result(test)
			testcase_id = testcase_id + 1
	return

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	global testcase_id
	vm_name = None
	mirror_dst_ip = None
	exit_on_failure = False
	try:
		opts, args = getopt.getopt(argv, "hv:i:e")
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
		elif opt == "-e":
			exit_on_failure = True
		else:
			usage()
	logfd = logger.open_log(logfile)
	if (vm_name == None or mirror_dst_ip == None):
		usage()

	suite = vca_test.SUITE("Mirror")
	suite.set_exit_on_failure(exit_on_failure)
	test_handlers = [
		pbm_single_mirror,
		pbm_multiple_acl_mirrors,
		vpm_single_mirror,
		pbm_vpm_single_mirror,
	]
	types = [ "default", "static", "reflexive" ]
	for type in types:
		test_args = {
			"suite" : suite,
			"ovs_path" : ovs_path,
			"br" : br,
			"logfd" : logfd,
			"vm_name": vm_name,
			"mirror_dst_ip" : mirror_dst_ip,
			"type" : type,
		}
		suite.run(test_handlers, test_args)
	suite.print_summary()

	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	testcase_id = 1
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

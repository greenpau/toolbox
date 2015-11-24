#!/usr/bin/python

import sys
import os
import getopt

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
import net

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import ovs_helper

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

def pbm_verify_flow_attrs__(pbm, mirror_dir, mirror_id, mirror_dst_ip):
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
	acl_dir = param['acl_dir']
	acl_type = param['acl_type']

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	pbm.local_create(acl_type, acl_dir)
	pbm.dump()
	pbm.show()
	pbm_dst_ip = str(pbm.get_dst_ip())
	if (mirror_dst_ip != pbm_dst_ip):
		print "Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + pbm_dst_ip + ")"
		pbm.local_destroy()
		return False
	else :
		print "Mirror Destination IP verification passed"
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	pbm_internal_name = str(pbm.get_internal_name())
	if (mirror_tunnel != pbm_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + pbm_internal_name + ")"
		pbm.local_destroy()
		return False
	else :
		print "Mirror Internal Name verification passed"
	passed = pbm_verify_flow_attrs__(pbm, acl_dir, mirror_id, mirror_dst_ip)
	pbm.local_destroy()
	return passed

def pbm_multiple_mirrors__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	acl_type = param['acl_type']

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	pbm.local_create(acl_type, "ingress")
	pbm.local_create(acl_type, "egress")
	pbm.dump()
	pbm.show()
	pbm_dst_ip = str(pbm.get_dst_ip())
	if (mirror_dst_ip != pbm_dst_ip):
		print "Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + pbm_dst_ip + ")"
		pbm.local_destroy()
		return False
	else :
		print "Mirror Destination IP verification passed"
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	pbm_internal_name = str(pbm.get_internal_name())
	if (mirror_tunnel != pbm_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + pbm_internal_name + ")"
		pbm.local_destroy()
		return False
	else :
		print "Mirror Internal Name verification passed"
	passed = pbm_verify_flow_attrs__(pbm, "ingress", mirror_id,
					 mirror_dst_ip)
	if (passed == False):
		pbm.local_destroy()
		return False
	passed = pbm_verify_flow_attrs__(pbm, "egress", mirror_id,
					 mirror_dst_ip)
	pbm.local_destroy()
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
			  'acl_dir' : acl_dir,
			  'acl_type' : acl_type,
			}
		testcase_desc = "Single ACL Mirror: " + acl_dir + " " + acl_type
		test = vca_test.TEST(testcase_id, testcase_desc,
				     pbm_single_mirror__, param)
		test.run()
		testcase_id = testcase_id + 1
	return testcase_id

def pbm_multiple_mirrors(ovs_path, br, logfd, vm_name,
		         mirror_dst_ip, acl_type, testcase_id):
	param = { 'ovs_path' : ovs_path,
		  'br' : br,
		  'logfd' : logfd,
	          'mirror_id': "9900",
		  'mirror_dst_ip': mirror_dst_ip,
		  'vm_name': vm_name,
		  'acl_type' : acl_type,
		}
	testcase_desc = "Multiple ACL Mirror: " + acl_type
	test = vca_test.TEST(testcase_id, testcase_desc,
			     pbm_multiple_mirrors__, param)
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
	mirror_dir = param['mirror_dir']

	vpm = vca_vpm.VPM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	vpm.local_create(mirror_dir)
	vpm.dump()
	vpm.show()
	vpm_dst_ip = str(vpm.get_dst_ip())
	if (mirror_dst_ip != vpm_dst_ip):
		print "Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + vpm_dst_ip + ")"
		vpm.local_destroy()
		return False
	else :
		print "Mirror Destination IP verification passed"
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	vpm_internal_name = str(vpm.get_internal_name())
	if (mirror_tunnel != vpm_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + vpm_internal_name + ")"
		vpm.local_destroy()
		return False
	else :
		print "Mirror Internal Name verification passed"
	vpm.local_destroy()
	return True

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
			  'mirror_dir' : mirror_dir,
			}
		testcase_desc = "Port Mirror: " + mirror_dir
		test = vca_test.TEST(testcase_id, testcase_desc,
				     vpm_single_mirror__, param)
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
	testcase_id = pbm_multiple_mirrors(ovs_path, br,
					   logfd, vm_name, mirror_dst_ip,
					   "default", testcase_id)
	testcase_id = vpm_single_mirror(ovs_path, br, logfd,
					vm_name, mirror_dst_ip, testcase_id)

	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

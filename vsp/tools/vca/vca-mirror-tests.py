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
	sys.exit(1)

def pbm_run_basic_test(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	mirror_id = param['mirror_id']
	mirror_dst_ip = param['mirror_dst_ip']
	vm_name = param['vm_name']
	acl_type = param['acl_type']
	acl_dir = param['acl_dir']

	pbm = vca_pbm.PBM(ovs_path, br, logfd, mirror_id, mirror_dst_ip,
			  vm_name)
	pbm.local_create(acl_type, acl_dir)
	pbm.dump()
	pbm.show()
	pbm_dst_ip = str(pbm.get_dst_ip())
	if (mirror_dst_ip != pbm_dst_ip):
		print "Mirror Destination IP verification failed (expected: " + mirror_dst_ip + ", got: " + pbm_dst_ip + ")"
	else :
		print "Mirror Destination IP verification passed"
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	pbm_internal_name = str(pbm.get_internal_name())
	if (mirror_tunnel != pbm_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + pbm_internal_name + ")"
	else :
		print "Mirror Internal Name verification passed"
	pbm.local_destroy()

def vpm_run_basic_test(param):
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
	else :
		print "Mirror Destination IP verification passed"
	mirror_tunnel = "mirror-t" + net.ipaddr2hex(mirror_dst_ip)
	vpm_internal_name = str(vpm.get_internal_name())
	if (mirror_tunnel != vpm_internal_name):
		print "Mirror Internal Name verification failed (expected: " + mirror_tunnel + ", got: " + vpm_internal_name + ")"
	else :
		print "Mirror Internal Name verification passed"
	vpm.local_destroy()

def main(argc, argv):
	testcase_id = 1
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	try:
		opts, args = getopt.getopt(argv, "h")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-h":
			usage()
		else:
			usage()
	logfd = logger.open_log(logfile)

	acl_types = [ "default" ]
	acl_dirs = [ "ingress", "egress" ]

	for acl_type in acl_types:
		for acl_dir in acl_dirs:
			param = { 'ovs_path' : ovs_path,
				  'br' : br,
				  'logfd' : logfd,
			          'mirror_id': "9900",
				  'mirror_dst_ip': "10.15.55.254",
				  'vm_name': "mvdcdev05-1-vm1",
				  'acl_type' : acl_type,
				  'acl_dir' : acl_dir,
				}
			testcase_desc = acl_type + " " + acl_dir + " ACL Mirror"
			test = vca_test.TEST(testcase_id, testcase_desc,
					     pbm_run_basic_test, param)
			test.run()
			testcase_id = testcase_id + 1

	mirror_dirs = [ "ingress", "egress" ]

	for mirror_dir in mirror_dirs:
		param = { 'ovs_path' : ovs_path,
			  'br' : br,
			  'logfd' : logfd,
			  'mirror_id': "9900",
			  'mirror_dst_ip': "10.15.55.254",
			  'vm_name': "mvdcdev05-1-vm1",
			  'mirror_dir' : mirror_dir,
			}
		testcase_desc = mirror_dir + " Port Mirror"
		test = vca_test.TEST(testcase_id, testcase_desc,
				     vpm_run_basic_test, param)
		test.run()
		testcase_id = testcase_id + 1

	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

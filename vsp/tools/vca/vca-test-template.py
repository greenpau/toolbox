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
import ovs_flows

# VCA classes
sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_test
import vca_vm
import vca_evpn

def usage():
	print "usage: " + progname + " [options]"
	print "options:"
	print "    -e: exitOnFailure=true"
	print "    -s <suite>: CSV of suite name(s) to run"
	print "    -t <testproc>: CSV of testproc name(s) to run"
	print "    -l: list all testprocs"
	sys.exit(1)

############################### HELPERS #####################################
def subtest_1(param):
	ovs_path = param['ovs_path']
	n_sub_tests = 0

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
def test_handler__(param):
	ovs_path = param['ovs_path']
	br = param['br']
	logfd = param['logfd']
	custom_action = param['custom_action']
	n_sub_tests = 0

	passed, n_sub_tests = subtest_1(param)
	n_sub_tests = n_sub_tests + n_this_sub_tests
	if (passed == False):
		pbm.local_destroy()
		return False, n_sub_tests
	return passed, n_sub_tests

def XXX_handler(test_args):
	suite = test_args["suite"]
	ovs_path = test_args["ovs_path"]
	br = test_args["br"]
	logfd = test_args["logfd"]
	global testcase_id
	global listing

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
			     test_handler__, param)
	if (suite.register_test(test) == True):
		if (listing == True):
			test.list()
		test.run()
		suite.assert_test_result(test)
		testcase_id = testcase_id + 1
	return

def run_XXX(br, logfd, ovs_path, ovs_vers, exit_on_failure, test_subset):
	global testcase_id
	suite = vca_test.SUITE("XXX")
	suite.register_test_subset(test_subset)
	suite.set_exit_on_failure(exit_on_failure)
	test_handlers = [
		XXX_handler,
	]
	testcase_id = 1
	suite.print_header()
	test_args = {
		"suite" : suite,
		"ovs_path" : ovs_path,
		"br" : br,
		"logfd" : logfd,
		"type" : type,
		"ovs_vers" : ovs_vers,
	}
	suite.run(test_handlers, test_args)
	suite.print_summary()


############################### MAIN #########################################
def validate_args(progname, suite,
		  vm_name, aux_vm_name,
		  mirror_dst_ip,
		  mirror_dst_port):
	success = True
	if (suite == "XXX"):
		success = False
	elif (suite == "all"):
		success = False
	return success

def main(argc, argv):
	ovs_path, hostname, os_release, logfile, br, vlan_id = ovs_helper.set_defaults(home, progname)
	global testcase_id, listing
	exit_on_failure = False
	ovs_vers = ovs_helper.get_ovs_version(ovs_path)
	suite_list = [ "all" ]
	test_subset = []
	try:
		opts, args = getopt.getopt(argv, "hes:t:l")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-h":
			usage()
		elif opt == "-l":
			listing = True
		elif opt == "-e":
			exit_on_failure = True
		elif opt == "-s":
			suite_list = arg.split(",")
		elif opt == "-t":
			test_subset = arg.split(",")
		else:
			usage()
	logfd = logger.open_log(logfile)
	print "Test Configuration:"
	print "Suite: " + str(suite_list)
	for suite in suite_list:
		if (validate_args(progname, suite,
				  vm_name, aux_vm_name, mirror_dst_ip,
				  mirror_dst_port) == False):
			exit(1)
		if (suite == "XXX"):
			run_XXX(br, logfd, ovs_path, ovs_vers, exit_on_failure,
				test_subset)
		else:
			run_XXX(br, logfd, ovs_path, ovs_vers, exit_on_failure,
				test_subset)
	
	exit(0)

if __name__ == "__main__":
	argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	testcase_id = 1
	listing = False
	home = os.environ['HOME']
	main(argc, sys.argv[1:])

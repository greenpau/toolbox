#!/usr/bin/python

import sys
import os
import getopt
import time
    
home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/vca")

import regular
import express
import quick

# generic utility classes
import logger
import net

def usage():
	print "usage: " + progname + " -t -b -r [-s|-p|-P|-S|-T|-R]"
	print "required parameters:"
	print "    -t <runtype>: type of run (express, regular, quick)"
	print "    -b <bed>: name of bed (mvcdcdev18, mvdcdev20)"
	print "    -r <release>: 0.0, 3.2 etc"
	print
	print "optional parameters:"
	print "    -s <suite>: name of suite (NsgResiliency, etc)"
	print "    -T <test>: name of testcase (NsgRgDbSyncMultipleSubnetsSameMac etc)"
	print "    -R <repeat-num>: number of times to repeat the test/suite"
	print "    -p <path>: absolute path of private image"
	print "    -C: cnaSim will be set to true (only for quick)"
	print "    -P <phystopo>: dctorOvs, nsg"
	print "    -S <subtopo>: default, dcExpress, dctorOvs, dctorOvsVxlan, rh7Vxlan, ubuntu1404, ubuntu1404Vxlan"
	sys.exit(1)

def main(argc, argv):
	testbed = ""
	pkg_path = ""
	suite = ""
	type = ""
	subtopo = ""
	rel = ""
	phystopo = ""
	cnaSim = False
	is_iso = False
	testcase = ""
	repeat = ""
	try:
		opts, args = getopt.getopt(argv, "ht:b:s:p:r:S:P:CT:R:")
	except getopt.GetoptError as err:
		print progname + ": invalid argument, " + str(err)
		usage()
	for opt, arg in opts:
		if opt == "-t":
			type = arg
		elif opt == "-b":
			testbed = arg
		elif opt == "-p":
			pkg_path = arg
		elif opt == "-s":
			suite = arg
		elif opt == "-T":
			testcase = arg
		elif opt == "-R":
			repeat = arg
		elif opt == "-r":
			rel = arg
		elif opt == "-S":
			subtopo = arg
		elif opt == "-P":
			phystopo = arg
		elif opt == "-C":
			cnaSim = True
		else:
			usage()
	if (testbed == ""):
		print "missing testbed parameter"
		usage
	if (rel == ""):
		print "missing release parameter"
		usage
	if (pkg_path == ""):
		print "missing package path"
		usage
	if (phystopo == ""):
		phystopo = "dctorOvs"
	if (phystopo == "nsg"):
		platform = phystopo
		is_iso = True
	else :
		platform = "dctor"
	if (type == "express") :
		if (subtopo == ""):
			subtopo = "dcExpress"
		regression = express.Express(testbed, pkg_path, phystopo,
			       		     subtopo, rel,
					     platform, is_iso, False)
	elif (type == "quick"):
		regression = quick.Quick(testbed, pkg_path, phystopo,
					 subtopo, rel, platform, is_iso, False)
		regression.set_cnaSim(cnaSim)
	elif (type == "regular"):
		regression = regular.Regular(testbed, pkg_path, phystopo,
					     subtopo, rel, platform, is_iso,
					     False)
	else:
		usage()
	regression.set_suite(suite)
	regression.set_test(testcase)
	regression.set_repeat(repeat)
	regression.run_private()


if __name__ == "__main__":
        argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])


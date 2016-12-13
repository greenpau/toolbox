#!/usr/bin/python

import sys
import os
import getopt
import time
    
home = os.environ['HOME']
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
sys.path.append("/usr/local/openvswitch/pylib/vca")
sys.path.append("/usr/local/openvswitch/pylib/regress")

import regular
import express
import quick

# generic utility classes
import logger
import net

def usage():
	print "usage: " + progname + " -t -b -r [-e|-s|-p|-P|-S|-T|-R|-d|-D|-K|-A]"
	print "required parameters:"
	print "    -t <runtype>: type of run (express, regular, quick)"
	print "    -b <bed>: name of bed (mvcdcdev18, mvdcdev20)"
	print "    -r <release>: 0.0, 3.2 etc"
	print
	print "optional parameters:"
	print "    -e: set exitOnFailure true in the regression run"
	print "    -s <suite>: name of suite (NsgResiliency, etc)"
	print "    -c <custom gash>: custom gash repo (xzhao025/gash:noPg)"
	print "    -T <test>: name of testcase (NsgRgDbSyncMultipleSubnetsSameMac etc)"
	print "    -R <repeat-num>: number of times to repeat the test/suite"
	print "    -p <path>: absolute path of VRS private image"
	print "    -d <path>: relative path of Device global image"
	print "    -K <path>: relative path of Kontroller global image"
	print "    -D <path>: relative path of Director global image"
	print "    -l <path>: local path of VRS private image"
	print "    -C: cnaSim will be set to true (only for quick)"
	print "    -P <phystopo>: dctorOvs, nsg"
	print "    -S <subtopo>: default, dcExpress, dctorOvs, dctorOvsVxlan, rh7Vxlan, ubuntu1404, ubuntu1404Vxlan"
	print "    -A <addl-params>: additional non-std regression params if any"
	sys.exit(1)

def main(argc, argv):
	testbed = ""
	pkg_path = ""
	vrs_image_path = ""
	vrs_local_path = ""
	vsd_image_path = ""
	vsc_image_path = ""
	suite = ""
	type = ""
	subtopo = ""
	rel = ""
	phystopo = ""
	cnaSim = False
	is_iso = False
	eof = False
	testcase = ""
	repeat = ""
	custom_gash = ""
	addl_params = ""
	try:
		opts, args = getopt.getopt(argv, "l:het:b:s:p:r:S:P:CT:R:c:d:A:D:K:")
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
		elif opt == "-d":
			vrs_image_path = arg
		elif opt == "-l":
			vrs_local_path = arg
		elif opt == "-D":
			vsd_image_path = arg
		elif opt == "-K":
			vsc_image_path = arg
		elif opt == "-s":
			suite = arg
		elif opt == "-T":
			testcase = arg
		elif opt == "-R":
			repeat = arg
		elif opt == "-e":
			eof = True
		elif opt == "-r":
			rel = arg
		elif opt == "-S":
			subtopo = arg
		elif opt == "-P":
			phystopo = arg
		elif opt == "-C":
			cnaSim = True
		elif opt == "-c":
			custom_gash = arg
		elif opt == "-A":
			addl_params = ' ' + arg
		else:
			usage()
	if (testbed == ""):
		print "missing testbed parameter"
		usage
	if (rel == ""):
		print "missing release parameter"
		usage
	if (vrs_image_path != ""):
		pkg_path = ""
	elif (pkg_path == ""):
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
			if (phystopo == "nsg"):
				subtopo = None
			else:
				subtopo = "dcExpress"
		regression = express.Express(testbed, pkg_path, vrs_image_path,
					     phystopo, subtopo, rel,
					     platform, is_iso, eof,
					     vsd_image_path, vsc_image_path)
	elif (type == "quick"):
		regression = quick.Quick(testbed, pkg_path, vrs_image_path,
					 phystopo, subtopo, rel, platform,
					 is_iso, eof,
					 vsd_image_path, vsc_image_path)
		regression.set_cnaSim(cnaSim)
	elif (type == "regular"):
		regression = regular.Regular(testbed, pkg_path, vrs_image_path,
					     phystopo, subtopo, rel, platform,
					     is_iso, eof,
					     vsd_image_path, vsc_image_path)
	else:
		usage()
	regression.set_suite(suite)
	regression.set_test(testcase)
	regression.set_repeat(repeat)
	regression.set_custom_gash(custom_gash)
	regression.set_addl_params(addl_params)
	regression.set_vrs_local_path(vrs_local_path)
	regression.run_private()


if __name__ == "__main__":
        argc = len(sys.argv)
	progfile = os.path.basename(sys.argv[0])
	progname = progfile.split(".")[0]
	main(argc, sys.argv[1:])


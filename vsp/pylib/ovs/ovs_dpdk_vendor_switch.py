#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/dpdk")
import ovs_dpdk_vendor_01org
import ovs_dpdk_vendor_nicira

class SDK_OVS_Switch(object):
	def alloc_SDK_OVS(self, dpdk_vendor_name, vswitchd_path, br,
		          device_list):
		if (dpdk_vendor_name == "01.org"):
			return ovs_dpdk_vendor_01org.SDK_OVS_01org(dpdk_vendor_name, vswitchd_path, br, device_list)
		elif (dpdk_vendor_name == "nicira"):
		       return ovs_dpdk_vendor_nicira.SDK_OVS_nicira(dpdk_vendor_name, vswitchd_path, br, device_list)	

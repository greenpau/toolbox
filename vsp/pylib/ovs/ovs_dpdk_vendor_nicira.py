#!/usr/bin/python
import abc
import dpdk_helper
import ovs_dpdk_vendor

class SDK_OVS_nicira(ovs_dpdk_vendor.SDK_OVS):
	def __init__(self, ovs_dpdk_vendor_name, vswitchd_path, br,
		     dpdk_device_list):
		self.__n_mem_channels = 4
		self.__dp_type = "netdev"
		self.__port_type = "dpdk"
		self.__cpu_coremask = dpdk_helper.get_dpdk_cpu_coremask()
		self.br = br
		self.port_num_1 = 0
		self.start_index = self.port_num_1 + 1
		self.n_devices = len(dpdk_device_list.split(",")) + 1
		self.port_name_prefix = "dpdk"
		self.ovs_datapath_type = "datapath_type=" + self.__dp_type
		self.ovs_port_type = "type=" + self.__port_type
		self.vswitchd_cmdline = "sudo " + vswitchd_path + "/ovs-vswitchd --dpdk -c " + self.__cpu_coremask + " -n " + str(self.__n_mem_channels) + " --use-device " + dpdk_device_list + " -- --pidfile --detach"
		self.ofport_request_arg = ""
		self.bridge_type_arg = " -- set bridge " + self.br + " " + self.ovs_datapath_type

	def get_vswitchd_cmdline(self):
		return self.vswitchd_cmdline

	def get_ofport_request_arg(self, port_num):
		return self.ofport_request_arg

	def get_bridge_type_arg(self):
		return self.bridge_type_arg

	def get_port_type_arg(self, port_name):
		self.port_type_arg = " -- set interface " + port_name + " " + self.ovs_port_type + " " + self.ofport_request_arg

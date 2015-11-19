#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/vca")

import time
import shell
import vca_evpn
import json

class DHCP(vca_evpn.EVPN):
	def __show_dhcp_evpn_appctl(self, evpn_id, dhcp_cmd_hdr,
				    dhcp_cmd, need_br):
		if (need_br == True):
			cmd = [ self.appctl_path, "evpn/" + dhcp_cmd,
				self.br, evpn_id ]
		else :
			cmd = [ self.appctl_path, "evpn/" + dhcp_cmd,
				evpn_id ]
		shell.execute_hdr(dhcp_cmd_hdr + ":", cmd)
	def __show_dhcp_evpn_appctls(self, evpn_id):
		print "DHCP configuration in EVPN: " + evpn_id
		self.__show_dhcp_evpn_appctl(evpn_id, "DHCP Pools",
					     "dhcp-pool-show", True)
		self.__show_dhcp_evpn_appctl(evpn_id,
					     "DHCP Pool Tables",
					     "dhcp-table-show", True)
		self.__show_dhcp_evpn_appctl(evpn_id, "DHCP Tables",
					     "dhcp-table", False)
	def __show_dhcp_evpns(self):
		evpn_list = self.list_evpns()
		for evpn_id in evpn_list:
			self.__show_dhcp_evpn_appctls(evpn_id)

	def __show_dhcp_evpn_ovsdb_table(self, table):
		print "Content of table: " + table
		cmd = '/usr/bin/ovsdb-client transact \'["Open_vSwitch", {"op" : "select", "table" : "' + table + '", "where" : [] } ]\''
		output = shell.call_prog_as_is(cmd)
		parsed = json.loads(output)
		print json.dumps(parsed, indent=4, sort_keys=True)

	def __show_dhcp_evpn_ovsdb(self):
		self.__show_dhcp_evpn_ovsdb_table("Nuage_Evpn_Dhcp_Pool_Table")
		self.__show_dhcp_evpn_ovsdb_table("Nuage_Evpn_Dhcp_Pool_Dhcp_Entry_Table")

	def show(self):
		self.__show_dhcp_evpns()
		self.__show_dhcp_evpn_ovsdb()

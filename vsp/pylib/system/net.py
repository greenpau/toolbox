#!/usr/bin/python

import os
import sys
import subprocess
import shell

def __get_ifconfig_iface_ip(iface):
	ifconfig_out = shell.execute(["ifconfig", iface]).splitlines()
	for line in ifconfig_out:
		if line.find("inet addr") < 0:
			continue
		line_tok = line.split()
		ipaddr = line_tok[1].split(":")
		return ipaddr[1]
	for line in ifconfig_out:
		if line.find("inet ") < 0:
			continue
		line_tok = line.split()
		ipaddr = line_tok[1]
		return ipaddr

def __get_ip_iface_ip(iface):
	ip_out = shell.execute(["ip", "addr", "show", iface]).splitlines()
	for line in ip_out:
		if (line.find("inet ") < 0):
			continue
		line_tok = line.split()
		ip_subnet = line_tok[1]
		ipaddr = ip_subnet.split("/")
		return ipaddr[0]

def get_iface_ip(iface):
	if (os.path.exists("/sbin/ifconfig") == True):
		return __get_ifconfig_iface_ip(iface)
	elif (os.path.exists("/sbin/ip") == True):
		return __get_ip_iface_ip(iface)
	else:
		return None

def __set_ifconfig_iface_ip(iface, ip, netmask, logfd):
	cmd = [ "sudo", "ifconfig", iface, "up" ]
	shell.run_cmd("Bringing up " + iface, cmd, logfd)
	cmd = [ "sudo", "ifconfig", iface, ip, "netmask", netmask ]
	shell.run_cmd("Setting IP " + ip + " to " + iface, cmd, logfd)

def __set_ip_iface_ip(iface, ip, netmask, logfd):
	cmd = [ "sudo", "ip", "addr", "add", ip, "dev", iface ]
	shell.run_cmd("Setting IP " + ip + " to " + iface, cmd, logfd)

def set_iface_ip(iface, netmask, ip, logfd):
	if (os.path.exists("/sbin/ifconfig") == True):
		return __set_ifconfig_iface_ip(iface, ip, netmask, logfd)
	elif (os.path.exists("/sbin/ip") == True):
		return __set_ip_iface_ip(iface, ip, netmask, logfd)
	else:
		return None

def __get_ip_iface_mac(iface):
	ip_out = shell.execute(["ip", "addr", "show", iface]).splitlines()
	for line in ip_out:
		if (line.find("link/ether ") < 0):
			continue
		line_tok = line.split()
		mac = line_tok[1]
		return mac

def __get_ifconfig_iface_mac(iface):
	cmd = [ "sudo", "ifconfig", iface ]
	ifconfig_out = shell.execute(cmd).splitlines()
	for line in ifconfig_out:
		mac_token = 0
		if (line.find("HWaddr") >= 0):
			mac_token = 4
		elif (line.find("ether") >= 0):
			mac_token = 1
		else:
			continue
		line_tok = line.split()
		mac = line_tok[mac_token]
		return mac

def get_iface_mac(iface):
	if (os.path.exists("/sbin/ifconfig") == True):
		return __get_ifconfig_iface_mac(iface)
	elif (os.path.exists("/sbin/ip") == True):
		return __get_ip_iface_mac(iface)
	else:
		return None

def add_vlan(iface, logfd):
	vlan_tok = iface.split(".")
	mgmt_iface = vlan_tok[0]
	vlan_id = vlan_tok[1]
	cmd = [ "sudo", "vconfig", "add", mgmt_iface, vlan_id ]
	rc = shell.run_cmd("Creating vlan " + mgmt_iface + "." + vlan_id,
			   cmd, logfd);

def del_vlan(iface, logfd):
	vlan_tok = iface.split(".")
	mgmt_iface = vlan_tok[0]
	if (len(vlan_tok) > 1):
		vlan_id = vlan_tok[1]
	else:
	 	vlan_id = None
	if (vlan_id != None):
		cmd = [ "sudo", "vconfig", "rem", iface ]
		shell.run_cmd("Deleting vlan " + iface, cmd, logfd)

def __ip_route_add(iface, ip, subnet, netmask, logfd):
	val = subnet.split(".")
	subnet = val[0] + ".0.0.0"
	val = ip.split(".")
	gateway = val[0] + "." + val[1] + "." + val[2] + ".1"
	cmd = [ "sudo", "ip", "route", "add", subnet + "/32", "via", gateway,
       		"dev", iface ]
	shell.run_cmd("Setting ip route for iface " + iface + " ip " + ip,
		      cmd, logfd)

def __ifconfig_route_add(iface, ip, subnet, netmask, logfd):
	val = subnet.split(".")
	subnet = val[0] + ".0.0.0"
	val = netmask.split(".")
	netmask = val[0] + ".0.0.0"
	cmd = [ "sudo", "route", "add", "-net", subnet, "netmask", netmask,
       		"dev", iface ]
	shell.run_cmd("Setting route for iface " + iface + " ip " + ip,
		      cmd, logfd)

def route_add(iface, ip, subnet, netmask, logfd):
	if (os.path.exists("/sbin/route") == True):
		return __ifconfig_route_add(iface, ip, subnet, netmask, logfd)
	elif (os.path.exists("/sbin/ip") == True):
		return __ip_route_add(iface, ip, subnet, netmask, logfd)
	else:
		return None

def route_del(iface, ip, subnet, netmask, logfd):
	val = subnet.split(".")
	subnet = val[0] + ".0.0.0"
	val = netmask.split(".")
	netmask = val[0] + ".0.0.0"
	cmd = [ "sudo", "route", "del", "-net", subnet, "netmask", netmask,
       		"dev", iface ]
	shell.run_cmd("Removing route for iface " + iface + " ip " + ip,
		      cmd, logfd)

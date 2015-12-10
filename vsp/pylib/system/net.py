#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")

import os
import subprocess
import shell
import socket
import struct
import random

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
	cmd = [ "ifconfig", iface, "up" ]
	shell.run_cmd("Bringing up " + iface, cmd, logfd)
	cmd = [ "ifconfig", iface, ip, "netmask", netmask ]
	shell.run_cmd("Setting IP " + ip + " to " + iface, cmd, logfd)

def __set_ip_iface_ip(iface, ip, netmask, logfd):
	cmd = [ "ip", "addr", "add", ip, "dev", iface ]
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
	cmd = [ "ifconfig", iface ]
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
	cmd = [ "vconfig", "add", mgmt_iface, vlan_id ]
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
		cmd = [ "vconfig", "rem", iface ]
		shell.run_cmd("Deleting vlan " + iface, cmd, logfd)

def __ip_route_add(iface, ip, subnet, netmask, logfd):
	val = subnet.split(".")
	subnet = val[0] + ".0.0.0"
	val = ip.split(".")
	gateway = val[0] + "." + val[1] + "." + val[2] + ".1"
	cmd = [ "ip", "route", "add", subnet + "/32", "via", gateway,
       		"dev", iface ]
	shell.run_cmd("Setting ip route for iface " + iface + " ip " + ip,
		      cmd, logfd)

def __ifconfig_route_add(iface, ip, subnet, netmask, logfd):
	val = subnet.split(".")
	subnet = val[0] + ".0.0.0"
	val = netmask.split(".")
	netmask = val[0] + ".0.0.0"
	cmd = [ "route", "add", "-net", subnet, "netmask", netmask,
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
	cmd = [ "route", "del", "-net", subnet, "netmask", netmask,
       		"dev", iface ]
	shell.run_cmd("Removing route for iface " + iface + " ip " + ip,
		      cmd, logfd)

def ipaddr2hex(ip):
	a = ip.split('.')
	b = hex(int(a[0])) + hex(int(a[1])) + hex(int(a[2])) + hex(int(a[3]))
	b = b.replace('0x', '')
	return b

def checksum (msg) :
	if (len(msg)%2 != 0) :
		msg2 = msg + '\x00' 
	else :
		msg2 = msg
	s = 0
	for i in range (0, len(msg2), 2):
		w = (ord(msg2[i])<<8) + (ord(msg2[i+1]))
		s = s + w
	s = (s >> 16) + (s & 0xffff)
	s = (s >> 16) + (s & 0xffff)
	return ~s & 0xffff

def unpack_helper (fmt, data) :
	size = struct.calcsize(fmt)
	return struct.unpack(fmt, data[:size])+tuple([data[size:]])

def tcp_encap (ip_src, ip_dst, tcp_src_port, tcp_dst_port, tcp_payload) :
	ip_src_addr = socket.inet_aton (ip_src) 
	ip_dst_addr = socket.inet_aton (ip_dst)
	ip_proto = socket.IPPROTO_TCP
	# tcp_src_port 
	# tcp_dst_port
	tcp_seq = 0
	tcp_ack_seq = 0
	tcp_doff = 5 # 4 bit field, size of tcp header, 5 * 4 = 20 bytes
	# tcp flags
	tcp_fin = 1
	tcp_syn = 0
	tcp_rst = 0
	tcp_psh = 0
	tcp_ack = 0
	tcp_urg = 0
	tcp_window = 0
	tcp_csum = 0
	tcp_urg_ptr = 0
	tcp_offset_res = (tcp_doff << 4) + 0
	tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)
	tcp_hdr = struct.pack ('!HHLLBBHHH', tcp_src_port, tcp_dst_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window, tcp_csum, tcp_urg_ptr)
	tcp_len = len (tcp_hdr) + len (tcp_payload)
	pseudo_hdr = struct.pack ('!4s4sBBH', ip_src_addr, ip_dst_addr, tcp_csum, ip_proto, tcp_len) + tcp_hdr + tcp_payload
	tcp_csum = checksum (pseudo_hdr)
	tcp_hdr = struct.pack ('!HHLLBBHHH', tcp_src_port, tcp_dst_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window, tcp_csum, tcp_urg_ptr)
	return tcp_hdr+tcp_payload

def tcp_decap(tcp_data) :
	# (tcp_src_port, tcp_dst_port, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags, tcp_window, tcp_csum, tcp_urgptr, tcp_payload)
	return unpack_helper ('!HHLLBBHHH', tcp_data)

def ip_encap (ip_src, ip_dst, ip_proto, ip_payload) :
	# ip header 
	ip_ihl = 5
	ip_ver = 4
	ip_tos = 0
	ip_tot_len = 20 + len(ip_payload)
	ip_id = 12345
	ip_frag_off = 0
	ip_ttl = 255
	# ip_proto 
	ip_csum = 0
	ip_src_addr = socket.inet_aton(ip_src)
	ip_dst_addr = socket.inet_aton(ip_dst)
	ip_ihl_ver = (ip_ver << 4) + ip_ihl
	ip_hdr = struct.pack ('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_csum, ip_src_addr, ip_dst_addr)
	ip_csum = checksum (ip_hdr)
	ip_hdr = struct.pack ('!BBHHHBBH4s4s', ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_csum, ip_src_addr, ip_dst_addr)
	return ip_hdr+ip_payload

def ip_decap (ip_data) :
	# (ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_csum, ip_src_addr, ip_dst_addr, ip_payload)
	return unpack_helper ('!BBHHHBBH4s4s', ip_data)

def mac2bin(mac) : 
	return mac.replace(':','').decode('hex')

def eth_encap(eth_src, eth_dst, eth_type, eth_payload) :
	# eth header
	eth_type    = 0x0800
	eth_mac_src = mac2bin (eth_src)
	eth_mac_dst = mac2bin (eth_dst)
	eth_hdr = struct.pack ('!6s6sH', eth_mac_dst, eth_mac_src, eth_type)
	return eth_hdr+eth_payload

def eth_decap (eth_data) :
	# (eth_mac_dst, eth_mac_src, eth_type, eth_payload)
	return unpack_helper ('!6s6sH', eth_data)

def packet_create (cookie, eth_src, ip_src, eth_dst, ip_dst, ip_payload) :
	packet = eth_encap(eth_src, eth_dst, 0x0800,
			   ip_encap(ip_src, ip_dst, socket.IPPROTO_TCP,
				    tcp_encap(ip_src, ip_dst,
					      cookie, 0, ip_payload)))
    
	return packet

def send_packet(ovs_path, br, seq_no, src_mac, src_ip, dst_mac, dst_ip,
		dst_ofp_port, payload):
	random.seed(os.getpid())
	pkt_cookie = random.randint(1, 65535)
	ip_payload = payload + "-" + str(seq_no)
	pktstr = packet_create(pkt_cookie, src_mac, src_ip, dst_mac,
			       dst_ip, ip_payload)
	pkthex = pktstr.encode('hex')
	cmd = [ ovs_path + "/ovs-ofctl", "packet-out", br, dst_ofp_port,
		"resubmit(,4)", pkthex ]
	shell.execute(cmd)

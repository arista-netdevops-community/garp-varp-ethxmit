#!/usr/bin/python
# Copyright (C) 2024 Arista Networks, Inc. - Guillaume Vilar
# <guillaume.vilar@arista.com>

# Warning: Only IPV4 is supported.

import json
import sys
import subprocess
import os
import argparse

# Handling of arguments
parser = argparse.ArgumentParser(description='Send GARP packet in a VLAN or all VLANs')
# Add command-line arguments
parser.add_argument("vlan", type=str, nargs='?', help="VLAN in which the GARP should be send to.")
parser.add_argument('-a', action='store_true', help="Match all the VLANs configured with VARP or 'ip address virtual'")


# Run command and check output
def run_command(command):
    print("Running command: ['%s']" % command)
    output = os.system(command)
    if output != 0:
        print("ERROR - return code %d for command: ['%s']" % (output, command))

# Return vrf name in ns format; ex: default --> default ; blue --> ns-blue
def get_vrf_name_in_ns_format(vrf_name):
    if vrf_name != "default":
        vrf_name = "ns-" + vrf_name
    return vrf_name

# Return ethxmit command
def get_ethxmit_command(vrf, vip, vmac, int):
    cmd = "sudo ip netns exec " + vrf +  " ethxmit --ip-src=" + vip + " --ip-dst=255.255.255.255  -S " + vmac + " -D ff:ff:ff:ff:ff:ff --arp=reply " + int
    return cmd

# Get virtual MAC to advertise
def get_virtual_mac(show_ip_virtual_router_output):
    for mac in show_ip_virtual_router_output["virtualMacs"]:
        if mac["macType"] != "varp":
            continue
        virtual_mac_to_advertise =  mac["macAddress"]
        if virtual_mac_to_advertise == "" or virtual_mac_to_advertise == "00:00:00:00:00:00":
            print("ERROR - No virtual mac address found, aborting ('show ip virtual-router vrf all | json' returned an empty or '00:00:00:00:00:00' mac address).")
            sys.exit(1)
    print("virtual MAC is: ['%s']" % virtual_mac_to_advertise)
    return virtual_mac_to_advertise

# Sending GARP for VARP IP addresses
def handle_varp(show_ip_virtual_router_output, vmac, vlan_selected, is_all_vlan_selected):
    print("====== 1. VARP ======")
    for virtual_router in show_ip_virtual_router_output["virtualRouters"]:
        if not is_all_vlan_selected and vlan_selected.lower() != virtual_router["interface"].lower():
            print("Ignoring ['%s'] as the interface is not selected." % virtual_router['interface'])
            continue
        
        if virtual_router["state"] != "active":
            print("Ignoring ['%s'] as the interface is not up." % virtual_router['interface'])
            continue

        vrf = get_vrf_name_in_ns_format(virtual_router["vrfName"])
        interface_lower_case = virtual_router["interface"].lower()
        for vip in virtual_router["virtualIps"]:
            cmd = get_ethxmit_command(vrf, vip["ip"], vmac, interface_lower_case)
            run_command(cmd)


# Send GARP for 'ip address virtual' IP addresses
def handle_ip_address_virtual(show_ip_interface_output, vmac, vlan_selected, is_all_vlan_selected):
    print("====== 2. 'ip address virtual' ======")
    for interface in show_ip_interface_output["interfaces"].values():
        vip = interface["interfaceAddress"]["virtualIp"]["address"]

        # ignore the interface if it's not a virtual interface or not up.
        if vip == "0.0.0.0":
            print("Ignoring interface ['%s'] as it is not configured with 'ip address virtual'." % interface['name'])
            continue
        if interface["lineProtocolStatus"] != "up" or interface["interfaceStatus"] != "connected":
            print("Ignoring ['%s'] as the interface is not up." % interface['name'])
            continue
        
        if not is_all_vlan_selected and vlan_selected.lower() != interface["name"].lower():
            print("Ignoring ['%s'] as the interface is not selected." % interface["name"])
            continue

        # Modifying vrf part to match the linux 'namespace' way in case of non-default vrf
        vrf = get_vrf_name_in_ns_format(interface["vrf"])

        vlan_lower_case = interface["name"].lower()
        
        cmd = get_ethxmit_command(vrf, vip, vmac, vlan_lower_case)
        run_command(cmd)

if __name__ == "__main__":
    # Parse the command-line arguments
    args = parser.parse_args()
    # Parsing logic: ensure that either a vlan is provided, or -a is present
    if not args.a and args.vlan is None:
        parser.error("You must specify either a VLAN or use the '-a' flag to match all VLANs. Ex: 'python send_garp.py vlan10' or 'python send_garp.py -a'")

    # Access the values of the arguments
    vlan_selected = args.vlan
    is_all_vlan_selected = args.a

    # Loading output of commands
    show_ip_virtual_router_output = json.loads(subprocess.check_output(["FastCli", "-c", "show ip virtual-router vrf all | json"]))
    show_ip_interface_output = json.loads(subprocess.check_output(["FastCli", "-c", "show ip interface | json"]))
    
    vmac = get_virtual_mac(show_ip_virtual_router_output)
    handle_varp(show_ip_virtual_router_output, vmac, vlan_selected, is_all_vlan_selected)
    handle_ip_address_virtual(show_ip_interface_output, vmac, vlan_selected, is_all_vlan_selected)

#!/usr/bin/python
# Copyright (C) 2024 Arista Networks, Inc. - Guillaume Vilar
# <guillaume.vilar@arista.com>

# Warning: Only IPV4 is supported.

import json
import sys
import subprocess
import os
import argparse

ERROR_MESSAGE = "ERROR: You must specify either a VLAN, a list of VLANs or use the '-a' flag to match all VLANs configured. Ex: 'python send_garp.py vlan10', 'python send_garp.py vlan10,20', or 'python send_garp.py -a'"

# Handling of arguments
parser = argparse.ArgumentParser(description='Send GARP packet in a VLAN, a list of VLANs or all VLANs configured.')
# Add command-line arguments
parser.add_argument("vlan", type=str, nargs='?', help="Vlan in which the GARP should be sent to (ex: vlan100) or comma separated list of VLANs (ex: vlan100,200).")
parser.add_argument('-a', action='store_true', help="Match all the VLANs configured with VARP or 'ip address virtual'")


# Run command and check output
def run_command(vlan_name, command):
    print("Running command for '%s': '%s'" % (vlan_name, command))
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
    for virtual_router in show_ip_virtual_router_output["virtualRouters"]:
        if not is_all_vlan_selected and vlan_selected.lower() != virtual_router["interface"].lower():
            # Keeping that print for an eventual verbose mode.
            # print("Ignoring ['%s'] as the interface is not selected." % virtual_router['interface'])
            continue
        
        if virtual_router["state"] != "active":
            print("Ignoring ['%s'] as the interface is not up." % virtual_router['interface'])
            continue

        vrf = get_vrf_name_in_ns_format(virtual_router["vrfName"])
        interface_lower_case = virtual_router["interface"].lower()
        for vip in virtual_router["virtualIps"]:
            cmd = get_ethxmit_command(vrf, vip["ip"], vmac, interface_lower_case)
            run_command(interface_lower_case, cmd)


# Send GARP for 'ip address virtual' IP addresses
def handle_ip_address_virtual(show_ip_interface_output, vmac, vlan_selected, is_all_vlan_selected):
    for interface in show_ip_interface_output["interfaces"].values():
        vip = interface["interfaceAddress"]["virtualIp"]["address"]

        # ignore the interface if it's not a virtual interface or not up.
        if vip == "0.0.0.0":
            # Keeping that print for an eventual verbose mode.
            # print("Ignoring interface ['%s'] as it is not configured with 'ip address virtual'." % interface['name'])
            continue
        if not is_all_vlan_selected and vlan_selected.lower() != interface["name"].lower():
            # Keeping that print for an eventual verbose mode.
            # print("Ignoring ['%s'] as the interface is not selected." % interface["name"])
            continue
        if interface["lineProtocolStatus"] != "up" or interface["interfaceStatus"] != "connected":
            print("Ignoring ['%s'] as the interface is not up." % interface['name'])
            continue
        
        

        # Modifying vrf part to match the linux 'namespace' way in case of non-default vrf
        vrf = get_vrf_name_in_ns_format(interface["vrf"])

        vlan_lower_case = interface["name"].lower()
        
        cmd = get_ethxmit_command(vrf, vip, vmac, vlan_lower_case)
        run_command(vlan_lower_case, cmd)

if __name__ == "__main__":
    # Parse the command-line arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:  # Only print ERROR_MESSAGE if the exit code is not 0 (to avoid hitting that when displaying the help option.)
            print(ERROR_MESSAGE)
            parser.print_help()
        sys.exit(e.code)
    # Parsing logic: ensure that either a vlan is provided, or -a is present
    if not args.a and args.vlan is None:
        parser.error(ERROR_MESSAGE)

    # Access the values of the arguments
    vlans_inputs = args.vlan
    is_all_vlan_selected = args.a

    # vlans_inputs is a string with eventually commas to separate VLANs (ex: vlan100,vlan200).
    # If we want to support '-' notation, (ex: vlan100-150), that would be the location to do that.
    if vlans_inputs != None:
        vlan_selected_list = vlans_inputs.split(",")
        # Adding eventually "vlan" string in front of only digit vlan name (ex: ["vlan100", "200"] --> ["vlan100", "vlan200"])
        vlan_selected_list = [ "vlan"+item if item.isdigit() else item for item in vlan_selected_list ]

    # Loading output of commands
    show_ip_virtual_router_output = json.loads(subprocess.check_output(["FastCli", "-c", "show ip virtual-router vrf all | json"]))
    show_ip_interface_output = json.loads(subprocess.check_output(["FastCli", "-c", "show ip interface | json"]))
    
    vmac = get_virtual_mac(show_ip_virtual_router_output)

    # Rewriting the list of vlan selected in case 'all the vlan' option is selected ('-a' option).
    if is_all_vlan_selected:
        vlan_selected_list = ['all']
    
    # Go through each vlan selected, and handle both VARP and IP address virtual
    print("====== 1. VARP ======")
    for vlan_selected in vlan_selected_list:
        handle_varp(show_ip_virtual_router_output, vmac, vlan_selected, is_all_vlan_selected)
    print("====== 2. 'ip address virtual' ======")
    for vlan_selected in vlan_selected_list:
        handle_ip_address_virtual(show_ip_interface_output, vmac, vlan_selected, is_all_vlan_selected)

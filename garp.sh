#!/bin/bash
# coding=utf-8
# Copyright (C) 2024 Arista Networks, Inc. - Guillaume Vilar
# <guillaume.vilar@arista.com>

# This script is used to send GARP requests to the VLAN where the interface VLAN are configured with VARP command. 
# Ex: sudo ip netns exec ns-VRF_NAME ethxmit --ip-src=172.16.0.1 --ip-dst=255.255.255.255  -S 00:1c:73:00:dc:01 -D ff:ff:ff:ff:ff:ff --arp=request vlan2000

# It will send GARP requests for each interface in the switch in each respectives VRFs.
# The script will use the ethxmit tool to send the GARP requests. The ethxmit tool is a tool that allows to send Ethernet frames from a network namespace.

# Warning: Only IPV4 is supported.


IP_VIRTUAL_ROUTER_OUTPUT=$(FastCli -c "show ip virtual-router")
echo "$IP_VIRTUAL_ROUTER_OUTPUT"

VIRTUAL_MAC_ADDRESS=$(echo $IP_VIRTUAL_ROUTER_OUTPUT | grep "MAC address" | awk '{print $9}')
echo "Virtual MAC Address: $VIRTUAL_MAC_ADDRESS"

echo "$IP_VIRTUAL_ROUTER_OUTPUT" | grep "active" | while read -r line;
do
  
    echo " ######################### Processing: $line #########################"

    # Getting the protocol, to only process UP interfaces 
    PROTOCOL=$(echo $line | awk '{print $4}')
    echo "Protocol: $PROTOCOL"
    if [ "$PROTOCOL" != "U" ]; then
      echo "Interface is not UP, skipping"
      continue
    fi

    # Extract vlan interface name in lower case in Linux format (ex: Vl200 --> vlan200)
    INT_NAME_LOWER_CASE=$(echo $line | awk '{print $1}' |  sed 's/Vl/vlan/g')
    echo "Interface Name: $INT_NAME_LOWER_CASE"
    
    # Get the VRF where the interface is located in
    VRF_NAME=$(echo $line | awk '{print $2}')
    echo "VRF Name: $VRF_NAME"

    # Get the IP address of the interface
    IP_ADDR=$(echo $line | awk '{print $3}')
    echo "IP Address: $IP_ADDR"

    # Building final command
    if [ "$VRF_NAME" == "default" ]; then
      CMD="sudo ip netns exec $VRF_NAME ethxmit --ip-src=$IP_ADDR --ip-dst=255.255.255.255  -S $VIRTUAL_MAC_ADDRESS -D ff:ff:ff:ff:ff:ff --arp=request $INT_NAME_LOWER_CASE"
    else
        CMD="sudo ip netns exec ns-$VRF_NAME ethxmit --ip-src=$IP_ADDR --ip-dst=255.255.255.255  -S $VIRTUAL_MAC_ADDRESS -D ff:ff:ff:ff:ff:ff --arp=request $INT_NAME_LOWER_CASE"
    fi
    echo "Executing: $CMD"
    eval $CMD
done

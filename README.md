# GARP Request Script
This script, `send_garp.sh`, can be used to send broadcast Gratuitous ARP (GARP) requests in the VLAN where the SVIs are configured with VARP configuration. 
Example: 
```
ip virtual-router mac-address 00:1c:73:00:09:99
interface Vlan100
   no autostate
   vrf BLUE
   ip address 10.0.0.2/24
   ip virtual-router address 10.0.0.1
```
The GARP requests are sent for each SVI in their respective VRFs. The script uses the ethxmit tool to send the GARP requests.  
This is useful when we migrate from another FHRP protocol and the mac-address linked to the default gateway changes: the hosts will then be able to refresh their ARP entries, reducing the downtime of the migration.

# Usage
1. Copy the send_garp.sh script to the switches in the `/mnt/flash/` directory.
2. Complete the migration activity for the new SVI to be up and reachable from the network.
3. Execute the script as:
```
bash /mnt/flash/send_garp.sh
```

# Example of packets sent to the network: 
```
15:27:58.006002 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 100, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 10.0.0.1 is-at 00:1c:73:00:09:99, length 28

15:27:58.156925 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 400, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 10.0.40.1 is-at 00:1c:73:00:09:99, length 28
```

# Limitations
Currently, the script only supports IPv4.


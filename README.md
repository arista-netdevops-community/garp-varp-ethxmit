# Arista GARP Request Script
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
The GARP requests are sent for each SVI in their respective VRFs. The script uses the `ethxmit` command to send the GARP requests to all the interfaces part of the VLAN.  
This is useful when the mac-address linked to the default gateway changes (for example when migrating from another FHRP protocol), and we want all the hosts in the network to refresh their ARP entries to reduce the downtime of the migration.

# Pre-requisite: 
1. Have a user with access to the command `bash` and `sudo` command.  
Verification: 
```
enable
bash sudo ls /mnt/flash
```
> Note: The default `network-operator` role doesn't allow the `bash` command, and thus, a user that is assigned that role cannot execute the script.  

# Usage
1. Copy the `send_garp.sh` script to the switches in the `/mnt/flash/` directory.
2. Complete the migration activity for the new SVI to be up and reachable from the network.
3. Execute the script with the command:
```
run enable ; bash bash /mnt/flash/send_garp.sh
```

# Example of output
```
switch# run enable ; bash bash /mnt/flash/send_garp.sh
#enable
#bash bash /mnt/flash/send_garp.sh
Processing output: 
######################### 
 
IP virtual router is configured with MAC address: 001c.7300.0999
IP virtual router address subnet routes not enabled
IP router is not configured with Mlag peer MAC address
MAC address advertisement interval: 30 seconds

Protocol: U - Up, D - Down, T - Testing, UN - Unknown
          NP - Not Present, LLD - Lower Layer Down

Interface       Vrf           Virtual IP Address       Protocol       State 
--------------- ------------- ------------------------ -------------- ------
Vl100           default       10.0.0.1                 U              active
Vl400           default       10.0.40.1                U              active 
#########################

Virtual MAC Address: 001c.7300.0999 
 

Executing command: 'sudo ip netns exec default ethxmit --ip-src=10.0.0.1 --ip-dst=255.255.255.255  -S 001c.7300.0999 -D ff:ff:ff:ff:ff:ff --arp=reply vlan100'
Executing command: 'sudo ip netns exec default ethxmit --ip-src=10.0.40.1 --ip-dst=255.255.255.255  -S 001c.7300.0999 -D ff:ff:ff:ff:ff:ff --arp=reply vlan400'

```

# Example of packets sent to the network: 
```
15:27:58.006002 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 100, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 10.0.0.1 is-at 00:1c:73:00:09:99, length 28

15:27:58.156925 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 400, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 10.0.40.1 is-at 00:1c:73:00:09:99, length 28
```

# Limitations
Currently, the script only supports IPv4.


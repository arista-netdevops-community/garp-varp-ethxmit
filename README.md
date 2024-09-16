# Arista Send GARP Request Script
This script, `send_garp.py`, can be used to send broadcast Gratuitous ARP (GARP) requests in the VLAN where the SVIs are configured with VARP or 'ip address virtual' configuration.  
Example: 
```
ip virtual-router mac-address 00:1c:73:00:09:99
interface Vlan100
   vrf BLUE
   ip address 172.16.100.2/24
   ip virtual-router address 172.16.100.1
interface Vlan200
   vrf RED
   ip address virtual 172.16.200.1/24
```
The GARP requests are sent for each SVI in their respective VRFs. The script uses the `ethxmit` command to send the GARP requests to all the interfaces part of the VLAN.  
This is useful when the mac-address linked to the default gateway changes (for example when migrating from another FHRP protocol), and we want all the hosts in the network to refresh their ARP entries to reduce the downtime of the migration.

# Prerequisite: 
1. A user with access to the command `bash` and `sudo` command.  
Verification: 
```
enable
bash sudo ls /mnt/flash
```
> Note: The default `network-operator` role doesn't allow the `bash` command, and thus, a user that is assigned that role cannot execute the script.  



# Usage
1. Copy the `send_garp.py` script to the switches in the `/mnt/flash/` directory.
2. Complete the migration activity for the new SVI to be up and reachable from the network.
3. Execute the script with the command:
```
run enable ; bash python /mnt/flash/send_garp.py -a
```

It is also possible to specify the VLAN where the GARP will be sent in case we want to migrate one VLAN at a time, with the `vlan` keyword.  
Example: 
```
run enable ; bash python /mnt/flash/send_garp.py vlan100
```

Help message: 
```
$ python send_garp.py --help
usage: send_garp.py [-h] [-a] [vlan]

Send GARP packet in a VLAN or all VLANs.

positional arguments:
  vlan        VLAN in which the GARP should be send to.

optional arguments:
  -h, --help  show this help message and exit
  -a          Match all the VLANs configured with VARP or 'ip address virtual'
```


# Example of output
```
spine1#run enable ; bash python /mnt/flash/send_garp.py -a
#enable
#bash python /mnt/flash/send_garp.py -a
virtual MAC is: ['00:1c:73:00:09:99']
====== 1. VARP ======
Running command for 'vlan100': 'sudo ip netns exec ns-BLUE ethxmit --ip-src=172.16.100.1 --ip-dst=255.255.255.255  -S 00:1c:73:00:09:99 -D ff:ff:ff:ff:ff:ff --arp=reply vlan100'
====== 2. 'ip address virtual' ======
Running command for 'vlan200': 'sudo ip netns exec ns-RED ethxmit --ip-src=172.16.200.1 --ip-dst=255.255.255.255  -S 00:1c:73:00:09:99 -D ff:ff:ff:ff:ff:ff --arp=reply vlan200'
```

# Example of packets sent to the network: 
```
15:27:58.006002 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 100, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 172.16.100.1 is-at 00:1c:73:00:09:99, length 28

15:27:58.156925 00:1c:73:00:09:99 > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 46: vlan 200, p 0, ethertype ARP (0x0806), Ethernet (len 6), IPv4 (len 4), Reply 172.16.200.1 is-at 00:1c:73:00:09:99, length 28
```

# Limitations
Currently, the script only supports IPv4.


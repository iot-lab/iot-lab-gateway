# Second stage U-Boot script of the IoT-LAB Raspberry Pi 2/3/4 gateways.
#
# The first stage script of the SD card gets the address of the node from
# DHCP and loads this script from <node address>/boot.scr: on the site TFTP
# server, <node address> points to the boot files of the root filesystem
# image deployed for the node (kernel, device trees and this script).
#
# fdtfile is set by the Raspberry Pi U-Boot from the board revision,
# rootpath comes from the DHCP root-path option (NFS root of the node).

tftp ${kernel_addr_r} ${ipaddr}/zImage || reset
tftp ${fdt_addr_r} ${ipaddr}/${fdtfile} || reset

# The root filesystem is the read-only NFS export of the image, /sbin/init
# of the image stacks a RAM overlay on top of it.
setenv bootargs "root=/dev/nfs nfsroot=${rootpath},tcp ro rootwait ip=dhcp 8250.nr_uarts=1 console=ttyS0,115200 smsc95xx.macaddr=${ethaddr} lan78xx.macaddr=${ethaddr} net.ifnames=0 panic=15"
bootz ${kernel_addr_r} - ${fdt_addr_r} || reset

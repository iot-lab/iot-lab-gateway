# Gateway root filesystem image

The `rootfs` target of the repository `Dockerfile` builds the root filesystem
of the IoT-LAB gateways as an OCI image, based on Debian trixie. It replaces
the Yocto gateway images (iot-lab-yocto). The image is not run as a container:
iot-lab-install unpacks it on the site host, exports it read-only over NFS and the gateways
boot it as their root filesystem, with a RAM overlay on top of it.
Deployment is documented in iot-lab-install (`GATEWAY_ROOTFS.md`).

| Platform       | Gateways                                    |
|----------------|---------------------------------------------|
| `linux/arm/v7` | A8 (var-som-am35), Raspberry Pi 2, 3 and 4  |
| `linux/arm64`  | Raspberry Pi 5                              |

The Raspberry Pi 2/3/4 gateways keep booting a 32-bit kernel through the
U-Boot of their SD card, hence the `linux/arm/v7` image for them. The
Raspberry Pi 5 gateways netboot from their EEPROM bootloader.

## Build

The build uses Docker buildx.

### Prerequisite: ARM emulation

On an x86 host the steps of the ARM images that run on the target platform
(package installation, kernel installation) are emulated (qemu user mode):
the qemu binfmt handlers must be registered in the host kernel. Without them
the build fails at its first `RUN` with:

    exec /bin/sh: exec format error

Register them, either persistently (Debian/Ubuntu package, registered at
boot by systemd-binfmt):

    $ sudo apt install qemu-user-binfmt

or until the next reboot, without installing anything:

    $ docker run --privileged --rm tonistiigi/binfmt --install arm,arm64

Check that they are registered and that an ARM container runs:

    $ ls /proc/sys/fs/binfmt_misc/ | grep qemu      # qemu-arm, qemu-aarch64
    $ docker run --rm --platform linux/arm/v7 debian:trixie uname -m    # armv7l
    $ docker run --rm --platform linux/arm64 debian:trixie uname -m     # aarch64

The tools not packaged in Debian (`tools` stage: openocd, oml2...) are
cross-compiled on the build machine, with the Debian cross toolchain of the
target (`crossbuild-essential-armhf`, `crossbuild-essential-arm64`): only the
package installations run emulated. The following builds reuse the cached
layers.

### Build

    $ make rootfs-image-armhf A8_KERNEL_DIR=<iot-lab-yocto>/build-a8/tmp/deploy/images/var-som-am35
    $ make rootfs-image-arm64

These targets build one platform and load the image in the local Docker
daemon. Check its boot files:

    $ docker run --rm --platform linux/arm/v7 fitiotlab/iot-lab-gateway-rootfs:<tag> ls -l /boot/iotlab/*
    $ docker run --rm --platform linux/arm64 fitiotlab/iot-lab-gateway-rootfs:<tag> ls -l /boot/iotlab/rpi5

`make rootfs-push` builds both platforms and pushes the multi-platform image
to the registry (log in first with `docker login`):

    $ docker login
    $ make rootfs-push ROOTFS_TAG=<tag> A8_KERNEL_DIR=<...> A8_KERNEL_MTD_RW_DIR=<...>

The default buildx builder (`docker` driver) can't build or push
multi-platform images ("Multi-platform build is not supported for the docker
driver"): `rootfs-push` uses its own builder with the `docker-container`
driver, `iot-lab-multiarch` (`ROOTFS_BUILDER`), created on first use by
`make rootfs-builder`. The default builder is left as it is, the
`rootfs-image-*` targets keep loading their image in the local daemon. The
`docker-container` builder has its own build cache: the first push rebuilds
everything.

The kernel modules and `uImage` of the A8 gateways come from the iot-lab-yocto
`a8` target (`make TARGET=a8 build-kernel`): the A8 kernel needs
`CONFIG_OVERLAY_FS=y`.

Variables:

* `ROOTFS_IMAGE`: image name, `fitiotlab/iot-lab-gateway-rootfs` by default
* `ROOTFS_TAG`: image tag, `git describe` by default
* `A8_KERNEL_DIR`: deploy directory of the iot-lab-yocto `a8` target. The
  A8 gateway kernel (`uImage`, zImage with the device tree appended) is taken
  from there, and its modules (`modules-var-som-am35.tgz`) if the kernel has
  some: the current one is built without modules. Without it the image has no
  A8 kernel.
* `A8_KERNEL_MTD_RW_DIR`: deploy directory of the A8 kernel with writable
  NAND partitions (iot-lab-yocto `make TARGET=a8 build-kernel-mtd-rw`,
  `build-a8/tmp/deploy/images/var-som-am35-mtd-rw`), installed as
  `/boot/iotlab/a8/uImage-mtd-rw`. Booted on demand to update the A8
  bootloader (iot-lab-install `GATEWAY_ROOTFS.md`).
* `JLINK_DIR`: extracted Segger J-Link software for the target architecture,
  installed in `/usr/local/share/JLink`. It is not redistributable, so it is
  not downloaded by the build.

The tools that are not packaged in Debian (openocd 0.11 in `/usr/local` and
the development openocd in `/opt/openocd-dev`, oml2, control_node_serial,
ftdi-utils, edbg, ykushcmd, mjpg-streamer, cc2538-bsl, pycom-utils) are built
from pinned revisions (`ARG` lines of the `tools` stage of the `Dockerfile`).
The `rootfs` image and the development image (`dev` target, see `DOCKER.md`)
share the `tools` and `gateway` stages: same tools, same gateway
installation, the `rootfs` target adds the kernels and the system of a
netbooted gateway.

## Boot files

Each gateway type has its boot files in `/boot/iotlab/<type>` of the image,
copied by iot-lab-install to the site TFTP server:

| Type        | Files                                                        |
|-------------|--------------------------------------------------------------|
| `a8`        | `uImage` (and `uImage-mtd-rw`), loaded by the NAND U-Boot    |
| `rpi2/3/4`  | `boot.scr` (second stage U-Boot script), `zImage`, `*.dtb`   |
| `rpi5`      | `Image`, `bcm2712*.dtb`, `overlays/`, `config.txt`           |

The Raspberry Pi kernels come from the Raspberry Pi archive
(`linux-image-rpi-v7` for the Raspberry Pi 2/3/4, `linux-image-rpi-2712`).
The A8 kernel needs `CONFIG_OVERLAY_FS=y`.

## Boot sequence on the gateway

1. The bootloader gets the address and the NFS root path from DHCP, loads
   the kernel from the per-node TFTP directory and boots it with
   `root=/dev/nfs ip=dhcp`.
2. The kernel mounts the read-only NFS export of the image and runs
   `/sbin/init` (`files/usr/sbin/init`). It stacks a tmpfs overlay on top of
   the NFS root, pivots into the union and starts systemd.
   `iotlab.overlay_size=` on the kernel command line sets the overlay size
   (25% of the RAM by default).
3. `iotlab-boot-setup.service` sets the name resolution from the kernel DHCP
   configuration, the `nfsserver` and `networkgateway` host names, chrony
   (synchronized with the default router), mounts `/var/local/config` and
   `/iotlab/users` from the site NFS server and sets the host name.
4. `gateway-server-network.service` adds the open node addresses (gateways
   with several open nodes) and `gateway-server.service` starts the gateway
   REST server (`gateway-server-daemon`).

Everything written on the gateway outside the NFS mounts is in RAM and lost
at reboot: the journal and the gateway server logs are kept small for this
reason (`journald.conf.d/iotlab.conf`, `logrotate.d/gateway-server`).
The network is configured by the kernel only and must never be reconfigured
(the root filesystem is on NFS), so the image has no network manager and
keeps the kernel interface names (`eth0`).

The image has no ssh host keys and no authorized keys: iot-lab-install adds
the ones of the site when it deploys the image.

For the A8 NAND, the image has `fw_printenv`/`fw_setenv` (U-Boot
environment, `/etc/fw_env.config`) and the mtd-utils (`flash_erase`,
`nandwrite`, `nanddump`). Writing needs the `uImage-mtd-rw` kernel: the
NAND partitions are read-only with `uImage`.

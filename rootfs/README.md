# Gateway root filesystem image

The `rootfs` target of the repository `Dockerfile` builds the root filesystem
of the IoT-LAB gateways as an OCI image, `fitiotlab/iot-lab-gateway-rootfs`.
It replaces the Yocto gateway images (iot-lab-yocto). The image is not run as
a container: iot-lab-install unpacks it on the site host, exports it
read-only over NFS and the gateways boot it as their root filesystem, with a
RAM overlay on top of it. Deployment is documented in iot-lab-install
(`GATEWAY_ROOTFS.md`).

| Platform       | Gateways                                    |
|----------------|---------------------------------------------|
| `linux/arm/v7` | A8 (var-som-am35), Raspberry Pi 2, 3 and 4  |
| `linux/arm64`  | Raspberry Pi 5                              |

## Image stack

```
iot-lab-linux-base           (iot-lab-open-linux) netbooted node system,
 |                            kernels and boot files, IoT-LAB tools
 `-- iot-lab-gateway-rootfs  (this repository) gateway server and services
```

The image is the gateway layer on top of `fitiotlab/iot-lab-linux-base`,
built by iot-lab-open-linux and shared with the open Linux nodes. The base
image provides:

- Debian trixie, systemd, sshd, chrony, nfs-common, the A8 NAND tools
  (`fw_printenv`, `fw_setenv`, mtd-utils)
- `/sbin/init`: stacks a RAM overlay on the read-only NFS root and starts
  systemd
- `iotlab-boot-setup.service`: name resolution, `nfsserver` and
  `networkgateway` host names, time synchronization, node configuration
  directory (`/var/local/config`), host name
- the kernels and boot files of every gateway type in `/boot/iotlab/<type>`
  (A8 kernels from iot-lab-yocto, Raspberry Pi kernels from the Raspberry Pi
  archive), copied to the site TFTP server by iot-lab-install
- the IoT-LAB tools (openocd, oml2, control_node_serial, edbg, ykushcmd,
  mjpg-streamer...) and the label `org.iot-lab.linux-base.version`, inherited
  by the gateway image

This repository adds (`rootfs` target of the `Dockerfile`, files in
`rootfs/files`):

- the gateway server dependencies that are not in the base image (avarice,
  curl, mosquitto, rtl-sdr, uhubctl, J-Link with `JLINK_DIR`)
- the gateway code of this checkout (replacing the pinned one of the base
  image), its udev rules and `gateway-server-daemon`
- `iotlab-gateway-setup.service`: mounts `/iotlab/users` from the site NFS
  server, after `iotlab-boot-setup.service`
- `gateway-server-network.service`: open node addresses of the gateways with
  several open nodes
- `gateway-server.service`: the gateway REST server
- log rotation of the gateway server logs (`logrotate.d/gateway-server`,
  hourly), sudo rules of www-data, `start_dc_on`/`stop_dc_on`

## Build

The build uses Docker buildx. On an x86 host, the package installations of
the ARM image are emulated (qemu user mode): register the qemu binfmt
handlers first, otherwise the build fails with
`exec /bin/sh: exec format error`:

    $ sudo apt install qemu-user-binfmt     # or: docker run --privileged --rm tonistiigi/binfmt --install arm,arm64
    $ docker run --rm --platform linux/arm/v7 debian:trixie uname -m    # armv7l

### Base image

The build needs `fitiotlab/iot-lab-linux-base` for the target platform:
pulled from the registry, or built locally in iot-lab-open-linux (with the
A8 kernels of an iot-lab-yocto checkout for the armhf image):

    $ cd iot-lab-open-linux
    $ make base-armhf TAG=<base tag> IOTLAB_YOCTO_DIR=<iot-lab-yocto>
    $ make base-arm64 TAG=<base tag>

The gateway image has the kernels of the base image: select the base tag
whose kernels the gateways must boot.

### Gateway image

    $ make rootfs-image-armhf LINUX_BASE_TAG=<base tag>
    $ make rootfs-image-arm64 LINUX_BASE_TAG=<base tag>

These targets build one platform and load the image in the local Docker
daemon, `fitiotlab/iot-lab-gateway-rootfs:<git describe>`. A base image
built locally is used as is. Check the image:

    $ docker run --rm --platform linux/arm/v7 fitiotlab/iot-lab-gateway-rootfs:<tag> ls -l /boot/iotlab/*
    $ docker run --rm --platform linux/arm/v7 fitiotlab/iot-lab-gateway-rootfs:<tag> gateway-rest-server --help
    $ docker image inspect -f '{{ index .Config.Labels "org.iot-lab.linux-base.version" }}' \
          fitiotlab/iot-lab-gateway-rootfs:<tag>

`make rootfs-push` builds both platforms and pushes the multi-platform image
(`docker login` first):

    $ make rootfs-push ROOTFS_TAG=<tag> LINUX_BASE_TAG=<base tag>

The base image must then be in the registry for both platforms
(`make push-base` in iot-lab-open-linux): the multi-platform build runs in
its own buildx builder (`iot-lab-multiarch`, `docker-container` driver,
created by `make rootfs-builder`), which doesn't see the images of the local
Docker daemon. The default builder (`docker` driver) can't build
multi-platform images.

Variables:

* `ROOTFS_IMAGE`: image name, `fitiotlab/iot-lab-gateway-rootfs` by default
* `ROOTFS_TAG`: image tag, `git describe` by default
* `LINUX_BASE_IMAGE`, `LINUX_BASE_TAG`: base image,
  `fitiotlab/iot-lab-linux-base:latest` by default
* `ROOTFS_PLATFORMS`: platforms of `rootfs-push`,
  `linux/arm/v7,linux/arm64` by default
* `JLINK_DIR`: extracted Segger J-Link software for the target architecture,
  installed in `/usr/local/share/JLink`. It is not redistributable, so it is
  not downloaded by the build.

## Development and tests images

The same `Dockerfile` builds the images to run the gateway code in a
container (`DOCKER.md`, `DEVELOPER.md`), for the platform of the build
machine. They don't use the base image: the `tools` stage builds the
IoT-LAB tools (same pinned revisions as iot-lab-open-linux), the `gateway`
stage installs them with the gateway code.

| Target | Image | Make target |
|---|---|---|
| `dev` (default) | `fitiotlab/iot-lab-gateway` | `make build-docker-image` |
| `tests` | `fitiotlab/iot-lab-gateway-tests` | `make build-docker-image-test` |

The `tests` image adds the test tools (tox, gdb, valgrind) and runs the
commands as the user of the host (`tests/entrypoint.sh`): `make test`,
`BOARD=<board> make integration-test`.

## Boot sequence on the gateway

1. The bootloader gets the address and the NFS root path from DHCP, loads
   the kernel from the per-node TFTP directory and boots it with
   `root=/dev/nfs ip=dhcp`.
2. The kernel mounts the read-only NFS export of the image and runs
   `/sbin/init` (base image): it stacks a tmpfs overlay on the NFS root,
   pivots into the union and starts systemd. `iotlab.overlay_size=` on the
   kernel command line sets the overlay size (25% of the RAM by default).
3. `iotlab-boot-setup.service` (base image): name resolution, host names,
   chrony, `/var/local/config`, host name.
4. `iotlab-gateway-setup.service` mounts `/iotlab/users`.
5. `gateway-server-network.service` adds the open node addresses (gateways
   with several open nodes) and `gateway-server.service` starts the gateway
   REST server (`gateway-server-daemon`).

Everything written on the gateway outside the NFS mounts is in RAM and lost
at reboot: the journal (base image) and the gateway server logs are kept
small for this reason. The network is configured by the kernel only and
must never be reconfigured (the root filesystem is on NFS).

The image has no ssh host keys and no authorized keys: iot-lab-install adds
the ones of the site when it deploys the image.

For the A8 NAND, the base image has `fw_printenv`/`fw_setenv` and the
mtd-utils. Writing needs the `uImage-mtd-rw` kernel of the base image
(iot-lab-install `GATEWAY_ROOTFS.md`): the NAND partitions are read-only
with `uImage`.

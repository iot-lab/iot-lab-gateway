## Open Node specific setup

### CC2650 Launchpad

The firmware of the XDS110 programmer provided on the CC2650 launchpad must
be updated to be able to flash the board.

- Download Code Composer Studio 7 (CCS7) on [the TI website](https://software-dl.ti.com/ccs/esd/documents/ccs_downloads.html#code-composer-studio-version-7-downloads)
- Decompress the archive and run the setup script:
  ```
  $ tar xf CCS7.4.0.00015_linux-x64.tar.gz
  $ cd CCS7.4.0.00015_linux-x64
  ```
- Install CCS7:
  ```
  $ ./ccs_setup_linux64_7.4.0.00015.bin
  ```

By default, CCS7 is installed in `~/ti/ccsv7`, you can now update the programmer
firmware:
- plug the board via USB
- Go the update tool directory:
  ```
  $ cd ~ti/ccsv7/ccs_base/common/uscif/xds110
  ```
- Switch the programmer to DFU mode:
  ```
  $ ./xdsdfu -m
  ```
- Upload the update firmware (already provided in the directory):
  ```
  $ ./xdsdfu -f firmware.bin -r
  ```

The board is ready.

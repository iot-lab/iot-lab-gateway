Changelog
=========

Version 2.8.0
-------------

+ Open nodes
  - Generalize Linux open node support
  - New nrf52832-mdk open node
  - New Pycom open node, only MicroPython supported
  - New LoRaWAN gateway open node
  - Allow flashing of st-ionode while sleeping

+ Utils
  - Refactor programmer tools into a single and generic Programmer

Version 2.7.0
-------------

+ Open nodes
  - New nRF51DK open node
  - New nRF52840MDK open node
  - New FRDM_KW41Z open node
  - New Atmel SAMR30-XPro (samr30) open node
  - Rework inheritance of open nodes: add new NodeOpenOCDBase, NodeJLinkBase,
    NodeEdbgBase, etc. This factorize a lot of code between open nodes
  - node_microbit: fix issue in OpenOCD reset sequence

+ Control nodes
  - Use YepKit modules to control power of open nodes with cn_rpi3

+ Utils
  - Rework openocd_cmd and avrdude_cmd to automatically the right open node
    class
  - Introcuce ExternalProcess to manage background services such as
    serial_redirection
  - mjpg_streamer and rtl_sdr are now based on ExternalProcess
  - add mjpg_streamer_cmd, rtl_sdr_cmd and cc2538_cmd help cli tools

+ Tests and CI
  - add unittests for Zigduino, Firefly, Leonardo, NodeOpenOCDBase and
    NodeEdbgBase nodes
  - add unittests for cn_iotlab and cn_iotlabm3
  - add missing unittests as much as possible (too many to list)
  - test coverage now reaches 90% without integration and 98% with integration
  - all autotest firmwares now include the get_uid commands
  - pytest coverage options are moved from setup.cfg to tox.ini (bug with
    pycharm debugger)
  - codecov is no longer a dependency in tox for integration tests: it is
    installed by default on the gateways

* Misc
  - Remove robot_tests and roomba gateway code

Version 2.6.0
-------------

+ Introduce base classes for open and control nodes
+ Open nodes
  - New nRF52DK open node
  - New nRF52840DK open node
  - New B-L475E-IOT01A2 (st-iotnode) open node
  - Micro:bit is now flashed with openocd
+ Control nodes
  - New IoT-LAB M3 based control node
  - New RPI3 control node with support for open node power control
+ Tests and CI:
  - Tests suite is now run with pytest
  - Fix for code coverage with codecov and Travis
  - Tox: all requirements use local packages for integration tests (e.g WebTest
    package is not installed via the tox environment)
  - Make: tox posargs can be passed via an environment variable


Version 2.5.0
-------------

+ New Arduino-Zero opennode
+ New ST LRWAN1 opennode
+ New Microbit opennode
+ New Zigduino opennode
+ Support for EDBG flasher tool and use with samr21 and arduino-zero
+ Support for PyOCD flasher tool
+ Add docker image and Makefile utils for running full integration tests on a
  local computer
+ Open nodes serial port is now in /dev/iotlab/tty_ONXXX
+ Start MJPG-Streamer daemon (for use with camera on the gateway) only when
  available


Version 2.4.1
-------------

+ Increase flash timeout to 100s
+ Fix pylint 1.7 issues


Version 2.4.0
-------------

+ Update control node firmware to new version:
    - More reliable serial, allows faster monitoring measures
    - Fix 120ppm constant drift
+ Fix samr21 flash timeout
+ Add a logger for cli scripts, helps debugging on boards


Version 2.3.0
-------------

### Features ###

+ Add samr21-xpro board support
+ Autotests:
    - Verify that all open nodes features have been tested, should help detect
      missing tests in autotests.
    - Add a test that verifies only `leds_on` and `leds_off`.


Version 2.2.0
-------------

### Features ###

+ Verify firmware elf target before using them.
  Invalid firmware may be uploaded, mainly with custom nodes so fail early.
+ Reject concurrent requests on `gateway_manager` instead of waiting for
  termination. Ensures only one REST request is processed at a time.
  Prevent the server to be blocked and crash on many requests if one is stuck
  infinitely.
+ verify open nodes classes implementation for given AUTOTESTS in firmware.

### Bug fixing ###

- Ensure `serial_redirection` gets stopped. It rarely does not close on
  SIGTERM. So try several sigterms/sigint and then sigkill.
- Wait a bit before using leonardo tty when visible, as may not be ready.

### Tests ###

+ Release udev rules before running integration tests. Will allow running tests
  with new nodes implementation.
+ Catch all REST methods exceptions and display a stacktrace, will help debug
  errors instead of only showing the 500 error.
+ Fix permissions just before running integration tests to make it work when
  doing `release python_test`.
+ Add `post_install` and `udev_rules_install` setup.py and fabric commands.


Version 2.1.1
-------------

+ Fix: `node_leonardo` wait tty ready, add some delay.


Version 2.1.0
-------------

### Bug fixing ###

* Add a timeout for flashing/reset nodes.
* Do terminate or kill for `cn_serial_interface` as it sometimes does not stop.

### Features ###

* Upgrade to oml2.11 and rebuild oml header at each compilation.
* Put openocd 'target/stm32f1x.cfg' as an option as it not required for all
  nodes. Wont be needed for samr21x-pro nodes.

### Tests ###

* Use texstfixtures.LogCapture for testing logs instead of mock.
* Fix integration tests with openocd-0.9
* Don't crash autotest on no return from 'echo'


Version 2.0.1
-------------

+ Fix Pylint 1.5 messages


Version 2.0.0
-------------

 + Reorganize all 'nodes' implementation to makes adding new archis easier.
   Architectures specific code is now in `open_nodes` with one module per node.
   (Romain Jayles)
 + Use a `serial_redirection` for a8 nodes boot debug.
 + Disable Battery charge on control node. Batteries are now removed.

### Add new architectures support ###

 + HiKoB Fox
 + Arduino Leonardo

### Tests ###

 + Use WebTest for rest server, this tests that the correct REST method is used
 + Improve `integration_fabfile.py` to run on all hosts by default and run all in
   one command.
 + Run c tests from 'tox'


Version 1.0.0
-------------

 + Reorganize code so `gateway_manager` depends on `nodes` which then depends
   on `utils`
 * Clean tests for new classes.
 * Allow select tests with nose attribute
 * Move 'cli' implementations in a 'utils' submodule


Version 0.4.0b
--------------

 * Node debugger
 * Adapt update_profile to experiment handler new request

 * Cleanup setup.py and use tox for managing tests

- 0.4.1b: Fix setup.py
- 0.4.2b: Fix static files not released at install
+ 0.4.3b: Replace log debug by log info on gateway_manager commands


Version 0.3
-----------

 * Support M3/A8 architecture
 * Experiment start/stop
 * Serial port redirection
 * Node flash/update
 * Control Node monitoring
 * Monitoring profile update

### Control Node features ###

 * Power management
 * Power consumption monitoring
 * Radio rssi monitoring
 * Radio sniffer with ZEP encapsulation

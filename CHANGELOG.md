Changelog
=========


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


Version 0.4.0b
--------------

 * Node debugger
 * Adapt update_profile to experiment handler new request

 * Cleanup setup.py and use tox for managing tests

- 0.4.1b: Fix setup.py
- 0.4.2b: Fix static files not released at install
+ 0.4.3b: Replace log debug by log info on gateway_manager commands


Version 1.0.0
-------------

 + Reorganize code so `gateway_manager` depends on `nodes` which then depends
   on `utils`
 * Clean tests for new classes.
 * Allow select tests with nose attribute
 * Move 'cli' implementations in a 'utils' submodule


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

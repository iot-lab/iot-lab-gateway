Gateway code Python README
==========================


Code development
----------------

### File hierarchy ###

    |
    +---gateway_code: implementation of gateway_code
    |       |
    |       +---tests: unit tests
    |       +---integration: integration tests that require a real gateway
    |       +---static: default profiles, firmwares, openocd conf
    |
    +---roomba: roomba low level communication implementation
    |           (not included in the tests suites at the moment)
    |
    +---control_node_serial: C program talking to control node over serial
    |
    |
    +---bin: CLI scripts and init.d script
    |
    |
    +---tests_utils: stuff useful for tests
            |
            +---curl_scripts: curl test examples


### Deploying manually ###

Install all the `gateway code` on a gateway

    python setup.py release

It runs the `install` command and the `post_install` procedure.


Testing
-------

Tests can be run with the following commands:

    python setup.py nosetests
    python setup.py lint
    python setup.py pep8

They require having installed 'tests-utils/test-requirements.txt' to run

> Note: unit tests require oml.mytestbed.net v2.11 installed.

### Automated testing ###

    # runs all tests at once
    tox

    # To run on gateways a 'www-data' user
    tox -e integration

#### PC gateway test ###

Testing using your PC as a gateway requires creating a stub config directory.
Take example at `tests_utils/cfg_dir/` and make a copy adapted for your node.

Ensure that udev-rules are correctly installed to detect nodes.
See `python setup.py release` procedure mentionned in `INSTALL.md` and
do at least the udev-rules install part, or run the full release.

Then run

    tox -e local <config_directory_path>
    # Example with m3 node
    tox -e local tests_utils/cfg_dir/

The user running the command should be in the `dialout` group


Testing using your PC as a gateway requires creating a stub config directory.
Take example at `tests_utils/cfg_dir/` and make a copy adapted for your node.

Testing using your PC as a gateway is best done with the included Docker image (see `DOCKER.md`)

Ensure that udev-rules are correctly installed to detect nodes.
See `python setup.py release` procedure mentionned in `INSTALL.md` and
do at least the udev-rules install part, or run the full release.

Then run

    tox -e local <config_directory_path>
    # Example with m3 node
    tox -e local tests_utils/cfg_dir/

The user running the command should be in the `dialout` group


Server REST (testing)
---------------------

* launch server REST: `./server_rest.py localhost 8080`
* start experiment:   `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/clochette -F "firmware=@idle.elf" -F "profile=@tata.json"; echo`
* flash open node:    `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/open/flash -F "firmware=@idle.elf"; echo`

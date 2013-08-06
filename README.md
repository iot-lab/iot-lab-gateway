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
        |
        +---roomba: roomba low level communication implementation
        |           (not included in the tests suites at the moment)
        |
        +---control_node_serial: C program talking to control node over serial
        |
        |
        |
        +---static: static conf: default profiles, firmwares, openocd conf
        |
        +---bin: CLI scripts and init.d script
        |
        |
        |
        +---scripts_tests: scripts usefull for tests
                |
                +---curl_scripts: curl test examples
                +---install_pylint_with_brain.sh: install pylint and
                                                  pylint-brain extensions


### Running tests or deploying ###

Run unit tests, pylint and pep8:

        python setup.py tests


Run full integration tests (should be run on a gateway):

        python setup.py integration


Install all the `gateway code`

        python setup.py install



Server REST (testing)
---------------------

* launch server REST: `./server_rest.py localhost 8080`
* start experiment:   `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/clochette -F "firmware=@idle.elf" -F "profile=@tata.json"; echo`
* flash open node:    `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/open/flash -F "firmware=@idle.elf"; echo`

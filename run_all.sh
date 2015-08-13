#! /bin/bash
set -xe
tox
fab -f tests_utils/integration_fabfile.py python_test:integration,autotest -H leonardo-00-ci
fab -f tests_utils/integration_fabfile.py python_test:integration,autotest -H m3-00-ci
fab -f tests_utils/integration_fabfile.py python_test:integration,autotest -H a8-00-ci

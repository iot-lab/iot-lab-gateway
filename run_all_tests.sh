#! /bin/bash -x

python setup.py nosetests ; python setup.py lint ; coveragereport

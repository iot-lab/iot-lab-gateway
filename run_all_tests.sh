#! /bin/bash

python setup.py nosetests ; python setup.py lint ; coveragereport

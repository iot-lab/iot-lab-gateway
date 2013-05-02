#! /bin/bash -xe

python setup.py nosetests --cover-html $@
python setup.py lint

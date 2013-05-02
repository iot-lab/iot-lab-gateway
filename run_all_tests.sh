#! /bin/bash -x

python setup.py nosetests --cover-html $@
python setup.py lint

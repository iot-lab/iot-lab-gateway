#! /bin/bash -x

python setup.py nosetests --cover-html $@
python setup.py lint
python setup.py pep8 | tee pep8.out

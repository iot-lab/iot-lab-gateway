#! /bin/bash -x

python setup.py nosetests --cover-html $@
python setup.py lint
python -mpep8 | tee pep8.out

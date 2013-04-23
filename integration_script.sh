#! /bin/sh

script_folder=$(dirname "$0")
echo "$script_folder"
cd "$script_folder"

source /etc/profile
pkill socat
rm -f coverage.xml nosetests.xml pylint.out
cp ~/python_missing_files/* .

git pull

set -e
python setup.py nosetests -i='*integration/*'
python setup.py lint --report | tee pylint.out

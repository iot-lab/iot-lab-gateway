#! /bin/sh


script_folder=$(dirname "$0")
base_folder=$(readlink -e ${script_folder}/..)

echo "$base_folder"
chmod -R o+w "$base_folder" # allow www-data to write tests output
cd "$base_folder"

source /etc/profile
pkill socat
rm -f coverage.xml nosetests.xml pylint.out

# cp ~/python_missing_files/* .   # missing files for 'requests' and 'pylint'
cp ~/python_missing_files/contextlib.py .   # missing for pylint

git pull

set -e

# run as the same user as bottle server
su  www-data   -c "source /etc/profile; PATH=./control_node_serial/:$PATH python setup.py build_cn_serial integration_tests $@"
python setup.py jenkins_lint
python -mpep8 | tee pep8.out

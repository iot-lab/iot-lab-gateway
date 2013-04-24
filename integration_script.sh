#! /bin/sh

script_folder=$(dirname "$0")
echo "$script_folder"
chmod -R o+w "$script_folder" # allow www-data to write tests output
cd "$script_folder"

source /etc/profile
pkill socat
rm -f coverage.xml nosetests.xml pylint.out
cp ~/python_missing_files/* .

git pull

set -e

# run as the same user as bottle server
su -c "source /etc/profile; python setup.py nosetests -i='*integration/*'" www-data
python setup.py lint --report | tee pylint.out

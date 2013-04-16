
source /etc/profile;
pkill socat;
cd fit-dev/gateway_code_python/;
rm -f coverage.xml nosetests.xml pylint.out;

cp ~/python_missing_files/* . ;
git pull;
python setup.py nosetests -i='*integration/*';
python setup.py lint --report | tee pylint.out;

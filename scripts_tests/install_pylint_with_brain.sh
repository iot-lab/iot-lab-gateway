#! /bin/bash -x

set -ex

WORKSPACE=$(pwd)

# now pypi is giving pylint 1.0
# force 0.27 as I didn't made the migration to new version of pylint and brain
pip install --quiet pylint==0.27

BRAIN=$(readlink -e "${WORKSPACE}")/pylint-brain
if [ ! -d "$BRAIN" ]; then
    hg clone https://bitbucket.org/logilab/pylint-brain "$BRAIN"
fi

# get right version of pylint-brain
cd "$BRAIN"
hg pull -u
hg checkout 9f94f90bc958 # newer versions caused problem some time ago
cd -


ORIG_BRAIN=$(python -c 'import logilab, os; print os.path.dirname(logilab.__file__) + "/astng/brain"')
rm -rf "$ORIG_BRAIN"
cp -r "$BRAIN/brain" "$ORIG_BRAIN"


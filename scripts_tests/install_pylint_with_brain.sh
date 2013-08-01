#! /bin/bash -x

WORKSPACE="$1"

pip install --quiet pylint

BRAIN=$(readlink -e "${WORKSPACE}/pylint-brain")
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
ln -s "$BRAIN/brain" "$ORIG_BRAIN"


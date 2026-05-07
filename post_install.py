#! /usr/bin/env python3

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""Post-installation system configuration script.

Replaces the distutils post_install command from the legacy setup.py.
Intended to be called via `hatch run release:deploy` after `pip install .`.

Usage:
    python post_install.py            # run all steps
    python post_install.py --only udev
    python post_install.py --only initd
    python post_install.py --only dialout
"""

import argparse
import os
import shutil
import subprocess
from glob import glob


def setup_initd():
    """Install and register the gateway-server-daemon init.d script."""
    init_script = "gateway-server-daemon"
    shutil.copy(os.path.join("bin", "init_script", init_script), "/etc/init.d/")
    os.chmod(os.path.join("/etc/init.d", init_script), 0o755)
    subprocess.check_call(
        [
            "update-rc.d",
            init_script,
            "start",
            "85",
            "2",
            "3",
            "4",
            "5",
            ".",
            "stop",
            "15",
            "0",
            "1",
            "6",
            ".",
        ]
    )


def setup_udev():
    """Install udev rules and reload the udev daemon."""
    for rule in glob(os.path.join("bin", "rules.d", "*.rules")):
        shutil.copy(rule, "/etc/udev/rules.d/")
    subprocess.check_call(["udevadm", "control", "--reload"])


def add_www_data_to_dialout():
    """Add the www-data user to the dialout group."""
    subprocess.check_call(["usermod", "-a", "-G", "dialout", "www-data"])


_STEPS = {
    "initd": setup_initd,
    "udev": setup_udev,
    "dialout": add_www_data_to_dialout,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--only", choices=list(_STEPS), help="Run only the specified step instead of all steps."
    )
    args = parser.parse_args()

    if args.only:
        _STEPS[args.only]()
    else:
        for step in _STEPS.values():
            step()
